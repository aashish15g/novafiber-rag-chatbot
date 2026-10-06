export async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : 'The request could not be completed. Check your input and try again.');
  }
  return data;
}

export function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function sourceCard(source, score) {
  const card = element('div', 'source-card');
  const link = element('a', '', `${source.source_id} · ${source.filename} · ${source.page_number ? `page ${source.page_number}` : `passage ${source.chunk_index + 1}`}`);
  // Only the application's source endpoint is permitted; never render provider URLs.
  const expected = `/api/documents/${source.document_id}/source`;
  if (source.source_url === expected || source.source_url === `${expected}#page=${source.page_number}`) {
    link.href = source.source_url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  }
  card.append(link);
  const details = element('details');
  details.append(element('summary', '', 'Read supporting passage'), element('p', '', source.excerpt));
  card.append(details);
  if (score !== undefined) card.append(element('p', '', `Similarity: ${score.toFixed(3)} · ranking signal, not confidence`));
  return card;
}

export function watchReadiness(callback) {
  const notice = document.getElementById('readiness');
  let stopped = false;
  async function check() {
    try {
      const response = await fetch('/api/ready');
      const state = await response.json();
      notice.textContent = state.ready
        ? state.generation_configured ? 'Your workspace is ready. Answers include links to their original policies.' : 'Retrieval is ready. Add GEMINI_API_KEY to .env and restart to enable chatbot answers.'
        : state.detail;
      notice.classList.toggle('error', state.embeddings === 'failed');
      callback(state);
    } catch {
      notice.textContent = 'Cannot reach the local server. Check that FastAPI is running.';
      notice.classList.add('error');
      callback({ready: false, generation_configured: false});
    }
    if (!stopped) setTimeout(check, 5000);
  }
  window.addEventListener('pagehide', () => { stopped = true; });
  check();
}
