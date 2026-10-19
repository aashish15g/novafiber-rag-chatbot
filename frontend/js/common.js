export async function api(url, options = {}) {
  const headers = new Headers(options.headers);
  if (options.method && !['GET', 'HEAD'].includes(options.method.toUpperCase())) {
    const csrf = document.cookie.split('; ').find(cookie => cookie.startsWith('csrf_token='));
    if (csrf) headers.set('X-CSRF-Token', decodeURIComponent(csrf.split('=')[1]));
  }
  const response = await fetch(url, {...options, headers, credentials: 'same-origin'});
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && !url.startsWith('/api/auth/login') && !url.startsWith('/api/auth/register')) {
      location.assign('/login?next=' + encodeURIComponent(location.pathname));
    }
    const detail = data.detail;
    const error = new Error(typeof detail === 'string' ? detail : 'The request could not be completed. Check your input and try again.');
    error.status = response.status;
    throw error;
  }
  return data;
}

export function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function renderAnswer(container, text) {
  // Render bold labels while keeping all model content as text, never HTML.
  const nodes = text.split(/(\*\*[^*\n]+\*\*)/g).map(part =>
    part.startsWith('**') && part.endsWith('**') && part.length > 4
      ? element('strong', '', part.slice(2, -2))
      : document.createTextNode(part));
  container.replaceChildren(...nodes);
}

export function sourceCard(source, score) {
  const card = element('div', 'source-card');
  const metadata = source.metadata || {};
  const link = element('a', '', `${source.source_id} · ${metadata.title || source.filename} · ${source.page_number ? `page ${source.page_number}` : `passage ${source.chunk_index + 1}`}`);
  // Only the application's source endpoint is permitted; never render provider URLs.
  const expected = `/api/documents/${source.document_id}/source`;
  const passage = `/sources/${source.document_id}/${source.chunk_id}#passage`;
  if (source.chunk_id && source.passage_url === passage) {
    link.href = passage;
  } else if (source.source_url === expected || source.source_url === `${expected}#page=${source.page_number}`) {
    link.href = source.source_url;
  }
  if (link.hasAttribute('href')) {
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  }
  card.append(link);
  if (metadata.article_id) card.append(element('p', 'citation-meta', `${metadata.article_id} · Version ${metadata.version} · Passage ${source.chunk_index + 1}`));
  const details = element('details');
  details.append(element('summary', '', 'Read supporting passage'), element('p', '', source.excerpt));
  card.append(details);
  if (score !== undefined) card.append(element('p', '', `Similarity: ${score.toFixed(3)} · ranking signal, not confidence`));
  return card;
}

export function icon(name) {
  const node = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  node.classList.add('icon');
  node.setAttribute('aria-hidden', 'true');
  const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
  use.setAttribute('href', `/static/assets/icons.svg#${name}`);
  node.append(use);
  return node;
}

export function mountShell({admin = false, authPage = false} = {}) {
  const header = element('header', 'site-header');
  const inner = element('div', 'container header-inner');
  const brand = element('a', 'brand');
  brand.href = '/';
  brand.setAttribute('aria-label', 'NovaFiber home');
  const mark = element('span', 'brand-mark');
  mark.append(icon('nova'));
  const name = element('span', 'brand-name', 'Nova');
  name.append(element('span', '', 'Fiber'));
  brand.append(mark, name);
  const nav = element('nav', 'header-nav');
  nav.setAttribute('aria-label', 'Primary navigation');
  const links = admin
    ? [['Customer view', '/', ''], ['Workspace', '/admin', 'active']]
    : [['Support center', '/', 'active'], ['Help topics', '/#support-topics', 'topics-link']];
  links.forEach(([label, href, className]) => {
    const link = element('a', className, label);
    link.href = href;
    if (className === 'active') link.setAttribute('aria-current', 'page');
    nav.append(link);
  });
  inner.append(brand, nav);
  header.append(inner);
  document.getElementById('site-header').replaceChildren(header);
  const footer = element('footer', 'site-footer');
  const footerInner = element('div', 'container footer-inner');
  const footerLinks = element('div', 'footer-links');
  [['Support center', '/']].forEach(([label, href]) => {
    const link = element('a', '', label);
    link.href = href;
    footerLinks.append(link);
  });
  footerInner.append(element('p', 'footer-note', 'NovaFiber · A fictional broadband company.'), footerLinks);
  footer.append(footerInner);
  document.getElementById('site-footer').replaceChildren(footer);
  if (!authPage) {
    api('/api/auth/me').then(user => {
      nav.append(element('span', 'account-label', user.email));
      if (user.role === 'admin' && !admin) {
        const workspace = element('a', '', 'Workspace');
        workspace.href = '/admin';
        nav.append(workspace);
      }
      const logout = element('button', 'quiet', 'Sign out');
      logout.type = 'button';
      logout.addEventListener('click', async () => {
        try {
          await api('/api/auth/logout', {method: 'POST'});
          location.assign('/login');
        } catch (error) { logout.textContent = error.message; }
      });
      nav.append(logout);
    }).catch(() => {});
  }
}

export function watchReadiness(callback, {admin = false} = {}) {
  const notice = document.getElementById('readiness');
  let stopped = false;
  let timer;
  async function check() {
    let pending = true;
    try {
      const response = await fetch('/api/ready');
      const state = await response.json();
      pending = !state.ready && state.embeddings !== 'failed';
      const available = state.ready && state.generation_configured;
      notice.textContent = available
        ? 'Nova is ready. Answers include links to the supporting policy.'
        : admin ? state.ready ? 'Retrieval is ready. Add GEMINI_API_KEY to .env and restart to enable chatbot answers.' : state.detail
        : state.embeddings === 'failed' || state.ready ? 'Nova is temporarily unavailable. Please try again later.' : 'Getting Nova ready. This may take a moment…';
      notice.dataset.state = available ? 'ready' : pending ? 'loading' : 'unavailable';
      notice.classList.toggle('error', state.embeddings === 'failed' || (!admin && state.ready && !available));
      const badge = document.getElementById('assistant-status');
      if (badge) {
        badge.classList.toggle('available', available);
        document.getElementById('assistant-status-text').textContent = available ? 'Available' : pending ? 'Connecting' : 'Unavailable';
      }
      callback(state);
    } catch {
      notice.textContent = admin ? 'Cannot reach the local server. Check that FastAPI is running.' : 'We’re having trouble connecting to Nova. Trying again…';
      notice.classList.add('error');
      callback({ready: false, generation_configured: false});
    }
    if (!stopped && pending) timer = setTimeout(check, 5000);
  }
  window.addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); });
  window.addEventListener('pageshow', event => { if (event.persisted) { stopped = false; check(); } });
  check();
}
