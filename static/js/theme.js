(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('#theme-toggle');
  if (!toggle) return;

  const savedTheme = () => {
    try { return localStorage.getItem('ecocycle-theme'); }
    catch (_) { return null; }
  };
  const setTheme = theme => {
    const dark = theme === 'dark';
    root.dataset.theme = dark ? 'dark' : 'light';
    toggle.setAttribute('aria-pressed', String(dark));
    toggle.setAttribute('aria-label', `${dark ? 'Dark' : 'Light'} theme is active. Switch to ${dark ? 'light' : 'dark'} theme.`);
    toggle.title = `${dark ? 'Dark' : 'Light'} theme active · switch to ${dark ? 'light' : 'dark'} theme`;
    toggle.querySelector('.theme-toggle-icon').textContent = dark ? '☀' : '☾';
    toggle.querySelector('.theme-toggle-text').textContent = dark ? 'Dark mode' : 'Light mode';
  };

  setTheme(root.dataset.theme || 'light');
  toggle.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    try { localStorage.setItem('ecocycle-theme', next); }
    catch (_) { /* Theme remains active for this page even when storage is unavailable. */ }
  });

  const preference = window.matchMedia?.('(prefers-color-scheme: dark)');
  preference?.addEventListener?.('change', event => {
    if (!savedTheme()) setTheme(event.matches ? 'dark' : 'light');
  });
})();
