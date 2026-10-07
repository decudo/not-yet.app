// Shared by every page: theme toggle, language menu, and the visit-count switch on /privacy/.
(() => {
  const root = document.documentElement;
  const store = (key, value) => { try { if (value === null) localStorage.removeItem(key); else localStorage.setItem(key, value); } catch (e) {} };

  // Theme. The choice is remembered in localStorage.
  const toggle = document.getElementById('theme-toggle');
  const themeColor = document.querySelector('meta[name="theme-color"]');
  if (toggle) {
    const apply = dark => {
      if (dark) root.dataset.theme = 'dark'; else delete root.dataset.theme;
      toggle.setAttribute('aria-pressed', String(dark));
      if (themeColor) themeColor.content = dark ? '#0C0B0A' : '#FBFAF8';
    };
    apply(root.dataset.theme === 'dark');
    toggle.addEventListener('click', () => {
      const dark = root.dataset.theme !== 'dark';
      apply(dark);
      store('notyet-theme', dark ? 'dark' : 'light');
    });
  }

  // Language menu (<details>): remember a pick so / no longer redirects; close on outside click or Escape.
  document.querySelectorAll('.lang').forEach(menu => {
    menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      store('notyet-lang', a.dataset.lang || a.getAttribute('hreflang'));
    }));
    document.addEventListener('click', e => { if (!menu.contains(e.target)) menu.open = false; });
    menu.addEventListener('keydown', e => {
      if (e.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); }
    });
  });

  // Visit counting opt-out (Umami's own flag, read by /assets/a.js).
  const optout = document.getElementById('optout');
  if (optout) {
    const off = () => { try { return !!localStorage.getItem('umami.disabled'); } catch (e) { return false; } };
    const sync = () => optout.setAttribute('aria-checked', String(!off()));
    sync();
    optout.addEventListener('click', () => { store('umami.disabled', off() ? null : '1'); sync(); });
  }
})();
