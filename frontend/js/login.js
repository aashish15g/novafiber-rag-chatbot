import {api, mountShell} from './common.js';

mountShell({authPage: true});
const form = document.getElementById('auth-form');
const button = document.getElementById('auth-submit');
const password = document.getElementById('password');
const status = document.getElementById('auth-status');
const toggle = document.getElementById('auth-switch');
let registering = false;

toggle.addEventListener('click', () => {
  registering = !registering;
  document.getElementById('auth-title').textContent = registering ? 'Get connected.' : 'Welcome back.';
  document.getElementById('auth-description').textContent = registering
    ? 'Create an account to ask Nova about your internet service.' : 'Sign in for help with your home internet.';
  button.textContent = registering ? 'Create account' : 'Sign in';
  toggle.textContent = registering ? 'Already have an account? Sign in' : 'New here? Create an account';
  password.minLength = registering ? 8 : 1;
  password.autocomplete = registering ? 'new-password' : 'current-password';
  status.textContent = '';
});

form.addEventListener('submit', async event => {
  event.preventDefault();
  button.disabled = true;
  toggle.disabled = true;
  status.textContent = '';
  const body = JSON.stringify({
    email: document.getElementById('email').value.trim(), password: password.value
  });
  const options = {method: 'POST', headers: {'Content-Type': 'application/json'}, body};
  try {
    if (registering) await api('/api/auth/register', options);
    const user = await api('/api/auth/login', options);
    const next = new URLSearchParams(location.search).get('next');
    const destination = next?.startsWith('/sources/') ? next
      : user.role === 'admin' ? '/admin' : '/';
    location.assign(destination);
  } catch (error) {
    status.textContent = error.message;
  } finally {
    button.disabled = false;
    toggle.disabled = false;
  }
});
