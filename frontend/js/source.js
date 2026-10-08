import {api, element, mountShell} from './common.js';

mountShell();
const status = document.getElementById('source-status');
const page = document.getElementById('source-page');
const [, , documentId, chunkId] = window.location.pathname.split('/');

async function load() {
  try {
    const source = await api(`/api/documents/${encodeURIComponent(documentId)}/chunks/${encodeURIComponent(chunkId)}`);
    const metadata = source.metadata;
    document.getElementById('source-title').textContent = metadata.title || source.filename;
    document.title = `${metadata.title || source.filename} · NovaFiber source`;
    document.getElementById('source-meta').textContent = [metadata.article_id,
      metadata.version ? `Version ${metadata.version}` : '',
      source.page_number ? `Page ${source.page_number}` : 'Text document',
      `Passage ${source.chunk_index + 1}`, metadata.last_reviewed ? `Reviewed ${metadata.last_reviewed}` : ''].filter(Boolean).join(' · ');
    const original = document.getElementById('original-source');
    const expected = `/api/documents/${documentId}/source`;
    if (source.source_url === expected || source.source_url === `${expected}#page=${source.page_number}`) {
      original.href = source.source_url;
      original.target = '_blank';
      original.rel = 'noopener noreferrer';
      original.hidden = false;
    }
    // Keep source offsets intact while reflowing PDF lines into readable sections.
    const headings = [...source.page_text.matchAll(/^\d+\. [^\n]+$/gm)];
    const highlights = [];
    let firstBodyHighlight;
    function appendRange(tag, className, start, end) {
      if (end <= start) return;
      const block = element(tag, className);
      const left = Math.max(start, source.char_start);
      const right = Math.min(end, source.char_end);
      if (left < right) {
        const mark = element('mark', 'source-highlight', source.page_text.slice(left, right));
        block.append(document.createTextNode(source.page_text.slice(start, left)), mark,
          document.createTextNode(source.page_text.slice(right, end)));
        highlights.push(mark);
        if (className === 'source-paragraph' && !firstBodyHighlight) firstBodyHighlight = mark;
      } else block.textContent = source.page_text.slice(start, end);
      page.append(block);
    }
    page.replaceChildren();
    if (headings.length) {
      appendRange('div', 'source-document-header', 0, headings[0].index);
      headings.forEach((heading, index) => {
        const end = heading.index + heading[0].length;
        appendRange('h2', 'source-section-heading', heading.index, end);
        appendRange('p', 'source-paragraph', end, headings[index + 1]?.index ?? source.page_text.length);
      });
    } else appendRange('p', 'source-paragraph', 0, source.page_text.length);
    const highlight = firstBodyHighlight || highlights[0];
    highlight.id = 'passage';
    highlight.tabIndex = -1;
    page.hidden = false;
    status.textContent = 'Supporting passage highlighted below.';
    highlight.focus({preventScroll: true});
    highlight.scrollIntoView({block: 'center'});
  } catch (error) {
    document.getElementById('source-title').textContent = 'Source unavailable';
    status.textContent = error.message;
    status.className = 'error-text';
  }
}

load();
