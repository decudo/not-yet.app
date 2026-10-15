// Start page motion: reveal on scroll, nav color, the watch tile and the rotation.
// The hero phones rise once on load in pure CSS (home.css).
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

  const nav = document.querySelector('.nav');
  const hero = document.getElementById('hero');
  let ticking = false;

  // The nav shares the hero's apricot ground until the hero has scrolled away.
  function update() {
    ticking = false;
    if (nav && hero) nav.classList.toggle('past', hero.getBoundingClientRect().bottom <= nav.offsetHeight);
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
