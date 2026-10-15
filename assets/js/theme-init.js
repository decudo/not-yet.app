// Runs in <head> before first paint: flags JS support and applies a remembered dark choice.
// Light is the default; only an explicit choice on the toggle switches to dark.
document.documentElement.classList.add('js');
try { if (localStorage.getItem('notyet-theme') === 'dark') document.documentElement.dataset.theme = 'dark'; } catch (e) {}
