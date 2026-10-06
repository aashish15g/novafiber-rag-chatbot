import {api, element, sourceCard, watchReadiness} from './common.js';

const library = document.getElementById('library');
const uploadButton = document.getElementById('upload');
const status = document.getElementById('upload-status');
let ready = false;
let busy = false;
let maxUploadMB = 10;

watchReadiness(state => {
  ready = state.ready;
  maxUploadMB = state.max_upload_mb || 10;
  document.getElementById('upload-limit').textContent = maxUploadMB;
  uploadButton.disabled = busy || !ready;
});

async function refresh() {
  try {
    const documents = await api('/api/documents');
    const indexed = documents.filter(doc => doc.status === 'ready');
    document.getElementById('document-count').textContent = indexed.length;
    document.getElementById('chunk-count').textContent = indexed.reduce((sum, doc) => sum + doc.chunk_count, 0);
    library.replaceChildren();
    if (!documents.length) library.append(element('div', 'empty-library', 'Your library is waiting. Upload your first policy to get started.'));
    documents.forEach(doc => {
      const row = element('div', 'document-row');
      row.append(element('div', 'file-icon', '▤'));
      const info = element('div', 'document-info');
      const name = element(doc.status === 'ready' ? 'a' : 'div', 'document-name', doc.filename);
      if (doc.status === 'ready') { name.href = doc.source_url; name.target = '_blank'; name.rel = 'noopener noreferrer'; }
      info.append(name, element('div', 'document-meta', `${doc.chunk_count} passages · ${new Date(doc.uploaded_at).toLocaleString()}`));
      if (doc.error) info.append(element('div', 'error-text', doc.error));
      row.append(info, element('span', `status-tag ${doc.status}`, doc.status));
      const remove = element('button', 'delete', 'Delete');
      remove.type = 'button';
      remove.addEventListener('click', async () => {
        if (!confirm(`Delete ${doc.filename} and all of its searchable passages?`)) return;
        remove.disabled = true;
        try { await api(`/api/documents/${doc.document_id}`, {method: 'DELETE'}); await refresh(); }
        catch (error) { status.textContent = error.message; status.className = 'error-text'; remove.disabled = false; }
      });
      row.append(remove);
      library.append(row);
    });
  } catch (error) { library.replaceChildren(element('div', 'error-text', error.message)); }
}

document.getElementById('refresh').addEventListener('click', refresh);
document.getElementById('upload-form').addEventListener('submit', async event => {
  event.preventDefault();
  const file = document.getElementById('policy-file').files[0];
  if (!file || busy || !ready) return;
  status.className = '';
  if (file.size > maxUploadMB * 1024 * 1024) { status.textContent = `The file exceeds ${maxUploadMB} MB.`; status.className = 'error-text'; return; }
  busy = true;
  uploadButton.disabled = true;
  status.textContent = 'Uploading, extracting text, and embedding passages locally. Please keep this page open…';
  const body = new FormData();
  body.append('file', file);
  try {
    const result = await api('/api/documents', {method: 'POST', body});
    status.textContent = result.duplicate ? 'This exact document is already in your library.' : `Ready to search: ${result.document.chunk_count} passages indexed with their source details.`;
    event.target.reset();
  } catch (error) { status.textContent = error.message; status.className = 'error-text'; }
  finally { busy = false; uploadButton.disabled = !ready; await refresh(); }
});

document.getElementById('retrieve-form').addEventListener('submit', async event => {
  event.preventDefault();
  const results = document.getElementById('retrieval-results');
  const question = document.getElementById('retrieve-question').value.trim();
  if (!question) return;
  const button = event.target.querySelector('button');
  button.disabled = true;
  results.replaceChildren(element('p', '', 'Searching your policy passages…'));
  try {
    const data = await api('/api/retrieve', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question})});
    results.replaceChildren();
    if (!data.passages.length) results.append(element('p', '', 'No indexed policy documents yet.'));
    data.passages.forEach(passage => results.append(sourceCard(passage, passage.score)));
  } catch (error) { results.replaceChildren(element('p', 'error-text', error.message)); }
  finally { button.disabled = false; }
});
refresh();
