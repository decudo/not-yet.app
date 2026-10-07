/* not-yet.app: loader for the site's self-hosted, cookieless Umami.

   The tracker origin is one constant in one first-party file. It points at the
   first-party host a.not-yet.app, a name of this site that fronts the
   maintainer's own Umami instance; changing where it points is one line here,
   plus the same host in the meta CSP of every page (tools/i18n/templates/).
   The app itself sends nothing anywhere; this counts website visits only. */
(function () {
  'use strict';

  var TRACKER_ORIGIN = 'https://a.not-yet.app';
  var WEBSITE_ID = 'ef98c1ad-12cf-4722-8144-9f16f4dcc08f';

  /* Not set up yet: load nothing (no request, no console error). */
  if (WEBSITE_ID.indexOf('TODO') === 0) return;

  /* Umami's own opt-out (switch on /privacy/). With it set, the script is not even fetched. */
  try {
    if (window.localStorage.getItem('umami.disabled')) return;
  } catch (e) {
    /* storage blocked: carry on; nothing here sets a cookie either way */
  }

  var s = document.createElement('script');
  s.defer = true;
  s.src = TRACKER_ORIGIN + '/s.js';
  s.setAttribute('data-website-id', WEBSITE_ID);
  s.setAttribute('data-domains', 'not-yet.app,www.not-yet.app');
  s.setAttribute('data-exclude-search', 'true');
  s.setAttribute('data-exclude-hash', 'true');

  /* NFC tag pages (/t/<id>): count the path /t/ only, never the tag ID. */
  if (/^\/t(\/|$)/.test(location.pathname)) {
    s.setAttribute('data-auto-track', 'false');
    s.onload = function () {
      if (window.umami) window.umami.track(function (p) { p.url = '/t/'; return p; });
    };
  }
  (document.head || document.documentElement).appendChild(s);
})();
