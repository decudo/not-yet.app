// Only on / (English): send a first-time visitor to their language, unless they picked one.
// Once a language was picked in the menu (site.js, key notyet-lang), / is never redirected again.
// Language pages never redirect, so there is no loop; crawlers see / as it is (hreflang does the rest).
(() => {
  const langs = ['de', 'es', 'fr', 'it', 'pt', 'ja', 'ko'];
  try { if (localStorage.getItem('notyet-lang')) return; } catch (e) { return; }
  if (/bot|crawl|spider|slurp|lighthouse/i.test(navigator.userAgent)) return;
  for (const tag of navigator.languages || [navigator.language || '']) {
    const code = tag.slice(0, 2).toLowerCase();
    if (code === 'en') return;
    if (langs.includes(code)) { location.replace('/' + code + '/' + location.hash); return; }
  }
})();
