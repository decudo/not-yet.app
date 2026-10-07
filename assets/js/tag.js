// NFC tag fallback and 404, used by /t/index.html and /404.html.
// GitHub Pages serves 404.html for every unknown path, so /t/<tagId> lands here
// when Not Yet isn't installed (with the app, iOS opens it before this page loads).
// Both pages carry one block per language; this shows the one for the path (/de/…),
// the language picked in the menu, or the browser language. English is the default.
(() => {
  const path = location.pathname;
  const m = /^\/t\/([0-9a-z]{6,32})\/?$/i.exec(path);
  const view = m || /^\/t\/?$/.test(path) ? 'tag' : 'notfound';
  const has = code => document.querySelector(`[data-view="${view}"][data-lang="${code}"]`);
  let pick = null;
  try { pick = localStorage.getItem('notyet-lang'); } catch (e) {}
  const wanted = [(/^\/([a-z]{2})\//.exec(path) || [])[1], pick,
    ...(navigator.languages || [navigator.language || '']).map(l => l.slice(0, 2).toLowerCase())];
  const code = wanted.find(c => c && has(c)) || 'en';
  const block = has(code);

  document.querySelectorAll('[data-view]').forEach(el => { el.hidden = el !== block; });
  document.documentElement.lang = block.getAttribute('lang');
  document.title = block.dataset.title;
  const skip = document.querySelector('.skip');
  if (skip) skip.textContent = block.dataset.skip;
  const toggle = document.getElementById('theme-toggle');
  if (toggle) toggle.setAttribute('aria-label', block.dataset.dark);
  if (code !== 'en') document.querySelectorAll('.brand').forEach(a => { a.href = `/${code}/`; });
  const menu = document.querySelector('.lang');
  if (menu) {
    menu.querySelector('summary .sr-only').textContent = block.dataset.menu;
    menu.querySelector('summary [aria-hidden]').textContent = code.toUpperCase();
    menu.querySelectorAll('a').forEach(a => {
      if (a.getAttribute('hreflang').startsWith(code)) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
    });
  }
  if (m) {
    const id = m[1].toLowerCase();
    block.querySelectorAll('.open-app').forEach(a => { a.href = 'notyet://t/' + id; });
    block.querySelectorAll('.tagid').forEach(el => { el.textContent = 'Tag ' + id; });
  }
})();
