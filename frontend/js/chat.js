import {api, element, sourceCard, watchReadiness} from './common.js';

const form = document.getElementById('chat-form');
const input = document.getElementById('question');
const button = document.getElementById('send');
const messages = document.getElementById('messages');
let ready = false;
let busy = false;

watchReadiness(state => {
  ready = state.ready && state.generation_configured;
  button.disabled = busy || !ready;
});

document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click', () => {
  input.value = button.dataset.question;
  input.focus();
}));

input.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    if (!busy && ready) form.requestSubmit();
  }
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question || busy || !ready) return;
  busy = true;
  button.disabled = true;
  document.getElementById('welcome')?.remove();
  messages.append(element('div', 'message question', question));
  input.value = '';
  const answer = element('div', 'message answer');
  answer.append(element('div', 'answer-label', 'POLICY DESK'), element('div', 'answer-copy', 'Finding relevant policies and preparing your answer…'));
  messages.append(answer);
  answer.scrollIntoView({behavior: 'smooth', block: 'nearest'});
  try {
    const result = await api('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question})});
    answer.querySelector('.answer-copy').textContent = result.answer;
    if (result.sources.length) {
      const sources = element('div', 'sources');
      result.sources.forEach(source => sources.append(sourceCard(source)));
      answer.append(sources);
    }
  } catch (error) {
    answer.querySelector('.answer-copy').textContent = error.message;
    answer.classList.add('error-text');
    const retry = element('button', 'secondary', 'Retry this question');
    retry.type = 'button';
    retry.addEventListener('click', () => { input.value = question; form.requestSubmit(); });
    answer.append(retry);
  } finally {
    busy = false;
    button.disabled = !ready;
    input.focus();
  }
});
