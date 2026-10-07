// Start page motion: reveal on scroll, lit statement, nav color, the day phone, the watch tile and the rotation.
// The hero fan opens once on load in pure CSS (home.css).
// With prefers-reduced-motion everything stays static and fully visible.
(() => {
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hasIO = 'IntersectionObserver' in window;

  // Reveal and strike-through: only elements below the first screen start hidden.
  if (!calm && hasIO) {
    const once = (selector, cls, options, below) => {
      const io = new IntersectionObserver(entries => entries.forEach(e => {
        if (e.isIntersecting) { e.target.classList.remove(cls); io.unobserve(e.target); }
      }), options);
      document.querySelectorAll(selector).forEach(el => {
        if (el.getBoundingClientRect().top > innerHeight * below) { el.classList.add(cls); io.observe(el); }
      });
    };
    once('.reveal', 'pre', { rootMargin: '0px 0px -8% 0px' }, 1);
    once('.line', 'pre-strike', { threshold: .8 }, .8);
  }

  // Statement: split into words that light up with scroll progress.
  const statement = document.getElementById('statement');
  const words = [];
  if (statement && !calm) {
    // Japanese has no spaces between words: let the browser find the words.
    const lang = document.documentElement.lang;
    const seg = /^(ja|zh)/.test(lang) && 'Segmenter' in Intl ? new Intl.Segmenter(lang, { granularity: 'word' }) : null;
    const parts = text => seg ? [...seg.segment(text)].map(s => s.segment) : text.split(/(\s+)/);
    (function split(node) {
      [...node.childNodes].forEach(n => {
        if (n.nodeType !== 3) { split(n); return; }
        const frag = document.createDocumentFragment();
        parts(n.textContent).forEach(t => {
          if (!t.trim()) { frag.append(t); return; }
          const s = document.createElement('span');
          s.className = 'w';
          s.textContent = t;
          words.push(s);
          frag.append(s);
        });
        n.replaceWith(frag);
      });
    })(statement);
    statement.classList.add('lit');
  }

  const nav = document.querySelector('.nav');
  const hero = document.getElementById('hero');
  const steps = [...document.querySelectorAll('.step')];
  const shots = [...document.querySelectorAll('#dayglass .shot')];
  const dots = [...document.querySelectorAll('.dots i')];
  let active = 0, ticking = false;

  function update() {
    ticking = false;
    const vh = innerHeight;
    if (!calm) {
      if (words.length) {
        const r = statement.getBoundingClientRect();
        const p = Math.min(1, Math.max(0, (vh * .85 - r.top) / (r.height + vh * .35)));
        const n = Math.round(p * words.length);
        words.forEach((w, i) => w.classList.toggle('on', i < n));
      }
    }
    // The nav shares the hero's apricot ground until the hero has scrolled away.
    if (nav && hero) nav.classList.toggle('past', hero.getBoundingClientRect().bottom <= nav.offsetHeight);
    // The day: the step closest to the middle of the screen drives the phone.
    let best = active, bestD = Infinity;
    steps.forEach((s, i) => {
      const r = s.getBoundingClientRect();
      const d = Math.abs(r.top + r.height / 2 - vh / 2);
      if (d < bestD) { bestD = d; best = i; }
    });
    if (best !== active) {
      active = best;
      steps.forEach((s, i) => s.classList.toggle('on', i === active));
      shots.forEach((s, i) => s.classList.toggle('on', i === active));
      dots.forEach((d, i) => d.classList.toggle('on', i === active));
    }
  }
  const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll);
  update();

  // Watch tile: start, step, DONE, three times while the watch is on screen, then it rests on the step.
  // Never with reduced motion; the step is the static picture.
  const watchShots = [...document.querySelectorAll('#watchface .shot')];
  if (watchShots.length && !calm && hasIO) {
    const HOLD = [2400, 2400, 1600];
    let w = 1, loops = 0, wTimer = null;
    const tick = () => {
      if (!document.hidden) {
        w = (w + 1) % watchShots.length;
        watchShots.forEach((s, k) => { s.classList.toggle('on', k === w); if (k === w) s.removeAttribute('aria-hidden'); else s.setAttribute('aria-hidden', 'true'); });
        if (w === 1 && ++loops === 3) { wTimer = null; return; }
      }
      wTimer = setTimeout(tick, HOLD[w]);
    };
    new IntersectionObserver(([e]) => {
      if (e.isIntersecting && !wTimer && loops < 3) wTimer = setTimeout(tick, HOLD[w]);
      if (!e.isIntersecting) { clearTimeout(wTimer); wTimer = null; }
    }, { threshold: .5 }).observe(document.getElementById('watchface'));
  }

  // Rotation demo: cycles Wheel, Ticket, Tally, Rocket (the app itself switches every few runs).
  // Auto-play runs only while the phone is on screen and the tab is visible, pauses under the mouse
  // or keyboard focus, and never runs with reduced motion (WCAG 2.2.2). A pick stays for about six seconds.
  const rotShots = [...document.querySelectorAll('#rotglass .shot')];
  const segs = [...document.querySelectorAll('.seg button')];
  const gesture = document.getElementById('gesture');
  if (!rotShots.length || !gesture) return;
  const EVERY = 2000, KEEP = 6000;
  let cur = 0, timer = null, visible = false, held = false, keepUntil = 0;

  function show(i) {
    if (i === cur) return;
    cur = i;
    rotShots.forEach((s, k) => { s.classList.toggle('on', k === i); if (k === i) s.removeAttribute('aria-hidden'); else s.setAttribute('aria-hidden', 'true'); });
    segs.forEach((b, k) => b.setAttribute('aria-pressed', String(k === i)));
    gesture.textContent = segs[i].dataset.gesture;
  }
  function sync(restart) {
    const run = !calm && visible && !held && !document.hidden;
    if (timer && (!run || restart)) { clearInterval(timer); timer = null; }
    if (run && !timer) timer = setInterval(() => { if (Date.now() >= keepUntil) show((cur + 1) % rotShots.length); }, EVERY);
  }
  function byHand(i) {
    gesture.setAttribute('aria-live', 'polite');
    show(i);
    keepUntil = Date.now() + KEEP - 200;
    sync(true);
  }
  segs.forEach((b, k) => b.addEventListener('click', () => byHand(k)));
  document.getElementById('shuffle').addEventListener('click', () => {
    let i;
    do { i = Math.floor(Math.random() * rotShots.length); } while (i === cur);
    byHand(i);
  });
  const box = document.querySelector('.rot');
  box.addEventListener('pointerenter', e => { if (e.pointerType === 'mouse') { held = true; sync(); } });
  box.addEventListener('pointerleave', () => { held = false; sync(); });
  box.addEventListener('focusin', e => { if (e.target.matches(':focus-visible')) { held = true; sync(); } });
  box.addEventListener('focusout', () => { held = false; sync(); });
  document.addEventListener('visibilitychange', () => sync());
  if (hasIO) {
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; sync(); }, { threshold: .5 })
      .observe(document.getElementById('rotglass'));
  }
})();
