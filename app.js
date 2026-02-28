/* app.js — MERIDIAN INTEL Dashboard Logic
   Real-time feed polling (60s), analytics tracking, theme/clock/mobile */
(function () {
  'use strict';

  const CGI_BIN = '__CGI_BIN__';

  const SESSION_ID = 'mi_' + Math.random().toString(36).substring(2, 15) +
                     Date.now().toString(36);

  const root = document.documentElement;
  const toggle = document.querySelector('[data-theme-toggle]');
  const iconMoon = toggle ? toggle.querySelector('.icon-moon') : null;
  const iconSun  = toggle ? toggle.querySelector('.icon-sun')  : null;

  let theme = 'dark';
  root.setAttribute('data-theme', theme);

  function updateThemeIcon() {
    if (!iconMoon || !iconSun) return;
    if (theme === 'dark') {
      iconMoon.style.display = 'block';
      iconSun.style.display  = 'none';
    } else {
      iconMoon.style.display = 'none';
      iconSun.style.display  = 'block';
    }
    updateMapTheme();
  }

  if (toggle) {
    toggle.addEventListener('click', () => {
      theme = theme === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', theme);
      updateThemeIcon();
    });
  }
  updateThemeIcon();

  const clockEl = document.getElementById('live-clock');
  const dateEl  = document.getElementById('live-date');
  const bannerTS = document.getElementById('banner-timestamp');
  const footerTS = document.getElementById('footer-timestamp');

  const MONTHS = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];

  function pad(n) { return String(n).padStart(2, '0'); }

  function getIST() {
    const now = new Date();
    const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
    const istMs = utcMs + (5 * 60 + 30) * 60000;
    return new Date(istMs);
  }

  function formatTime(d) { return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()); }
  function formatDate(d) { return pad(d.getDate()) + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear(); }
  function formatDateTime(d) { return formatDate(d) + ' / ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ' IST'; }

  function tickClock() {
    const ist = getIST();
    if (clockEl) clockEl.textContent = formatTime(ist);
    if (dateEl)  dateEl.textContent  = formatDate(ist);
  }
  tickClock();
  setInterval(tickClock, 1000);

  function updateMapTheme() {
    const svgMap = document.querySelector('.region-map');
    if (!svgMap) return;
    const bgRect = svgMap.querySelector('rect');
    if (!bgRect) return;
    bgRect.setAttribute('fill', theme === 'dark' ? '#0d1117' : '#f5f5f0');
  }

  const mobileMenuBtn = document.getElementById('mobile-menu-toggle');
  const sidebar = document.getElementById('sidebar');

  if (mobileMenuBtn && sidebar) {
    mobileMenuBtn.addEventListener('click', () => {
      const isOpen = sidebar.classList.toggle('open');
      mobileMenuBtn.setAttribute('aria-expanded', String(isOpen));
    });
  }

  const timelineList = document.querySelector('.timeline-list');
  const eventCountEl = document.getElementById('event-count');
  const feedStatusEl = document.getElementById('feed-status');
  const lastFetchEl  = document.getElementById('last-fetch-time');
  const nextFetchEl  = document.getElementById('next-fetch-countdown');
  const feedSourcesEl = document.getElementById('feed-sources-status');

  let lastKnownEntryIds = new Set();
  let fetchCountdown = 60;
  let isFirstLoad = true;
  let fetchInFlight = false;

  const PRIORITY_CLASS = { 'flash': 'flash', 'urgent': 'urgent', 'routine': 'routine' };
  const SOURCE_CLASS_MAP = {
    'REUTERS': 'media', 'BBC': 'media', 'ALJAZEERA': 'media', 'AP': 'media', 'TOI': 'media',
    'IDF': 'idf', 'IRGC': 'irgc', 'POTUS': 'potus', 'OSINT': 'osint', 'MEDIA': 'media'
  };

  function decodeHtmlEntities(text) {
    const ta = document.createElement('textarea');
    ta.innerHTML = text;
    return ta.value;
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function safeContent(text) {
    return escapeHtml(decodeHtmlEntities(text || ''));
  }

  function createTimelineEntry(entry, isNew) {
    const li = document.createElement('li');
    const priorityClass = PRIORITY_CLASS[entry.priority] || 'routine';
    const sourceClass = SOURCE_CLASS_MAP[entry.source_tag] || entry.source_class || 'media';
    li.className = 'timeline-entry ' + priorityClass;
    if (isNew && !isFirstLoad) li.classList.add('entry-new');
    li.innerHTML =
      '<div class="entry-meta">' +
        '<time class="entry-time" datetime="' + escapeHtml(entry.time || '') + '">' + escapeHtml(entry.time_display || '') + '</time>' +
        '<span class="entry-tag ' + priorityClass + '">' + escapeHtml(entry.priority || 'ROUTINE').toUpperCase() + '</span>' +
        '<span class="entry-source ' + sourceClass + '">' + escapeHtml(entry.source_tag || 'NEWS') + '</span>' +
      '</div>' +
      '<div class="entry-content">' + safeContent(entry.content || entry.title || '') + '</div>';
    return li;
  }

  function updateFeedStatus(status, sourcesStatus) {
    if (feedStatusEl) {
      if (status === 'loading') { feedStatusEl.textContent = 'FETCHING'; feedStatusEl.className = 'feed-status-value loading'; }
      else if (status === 'ok') { feedStatusEl.textContent = 'LIVE'; feedStatusEl.className = 'feed-status-value live'; }
      else { feedStatusEl.textContent = 'ERROR'; feedStatusEl.className = 'feed-status-value error'; }
    }
    if (lastFetchEl) lastFetchEl.textContent = formatDateTime(getIST());
    if (feedSourcesEl && sourcesStatus) {
      const sourceNames = Object.keys(sourcesStatus);
      let html = '';
      sourceNames.forEach(name => {
        const s = sourcesStatus[name];
        const cls = s === 'ok' ? 'online' : s === 'cached' ? 'warning' : 'offline';
        html += '<span class="feed-source-dot ' + cls + '" title="' + name.toUpperCase() + ': ' + s + '"></span>';
      });
      feedSourcesEl.innerHTML = html;
    }
  }

  async function fetchFeed() {
    if (fetchInFlight) return;
    fetchInFlight = true;
    updateFeedStatus('loading', null);
    try {
      const res = await fetch(CGI_BIN + '/feed.py', { method: 'GET', headers: { 'Accept': 'application/json' }, signal: AbortSignal.timeout(25000) });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      if (data.status !== 'ok' || !Array.isArray(data.entries)) throw new Error('Invalid response');
      const entries = data.entries;
      const newEntryIds = new Set(entries.map(e => e.id));
      if (timelineList) {
        const fragment = document.createDocumentFragment();
        entries.forEach(entry => { const isNew = !lastKnownEntryIds.has(entry.id); fragment.appendChild(createTimelineEntry(entry, isNew)); });
        timelineList.innerHTML = '';
        timelineList.appendChild(fragment);
      }
      if (eventCountEl) eventCountEl.textContent = String(data.entry_count || entries.length);
      if (data.updated_display) {
        if (bannerTS) bannerTS.textContent = data.updated_display;
        if (footerTS) footerTS.textContent = data.updated_display;
      }
      lastKnownEntryIds = newEntryIds;
      updateFeedStatus('ok', data.sources_status);
      isFirstLoad = false;
    } catch (err) {
      console.error('[MERIDIAN] Feed fetch error:', err);
      updateFeedStatus('error', null);
    } finally {
      fetchInFlight = false;
      fetchCountdown = 60;
    }
  }

  function tickCountdown() {
    fetchCountdown--;
    if (nextFetchEl) nextFetchEl.textContent = fetchCountdown + 's';
    if (fetchCountdown <= 0) fetchFeed();
  }

  fetchFeed();
  setInterval(tickCountdown, 1000);

  const analyticsViewsEl    = document.getElementById('analytics-total');
  const analyticsTodayEl    = document.getElementById('analytics-today');
  const analyticsActiveEl   = document.getElementById('analytics-active');
  const analyticsSessionsEl = document.getElementById('analytics-sessions');

  async function recordPageview() {
    try {
      await fetch(CGI_BIN + '/analytics.py', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event: 'pageview', path: window.location.pathname || '/', referrer: document.referrer || '', user_agent: navigator.userAgent || '', screen_width: window.screen.width || 0, session_id: SESSION_ID })
      });
    } catch (e) { /* silent */ }
  }

  async function sendHeartbeat() {
    try { await fetch(CGI_BIN + '/analytics.py?action=heartbeat&session_id=' + encodeURIComponent(SESSION_ID)); } catch (e) { /* silent */ }
  }

  async function fetchAnalytics() {
    try {
      const res = await fetch(CGI_BIN + '/analytics.py?action=summary');
      if (!res.ok) return;
      const data = await res.json();
      if (analyticsViewsEl) analyticsViewsEl.textContent = formatNumber(data.total_views || 0);
      if (analyticsTodayEl) analyticsTodayEl.textContent = formatNumber(data.today_views || 0);
      if (analyticsActiveEl) analyticsActiveEl.textContent = String(data.active_last_5min || 0);
      if (analyticsSessionsEl) analyticsSessionsEl.textContent = formatNumber(data.unique_sessions_today || 0);
    } catch (e) { /* silent */ }
  }

  function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return String(n);
  }

  recordPageview();
  fetchAnalytics();
  setInterval(sendHeartbeat, 120000);
  setInterval(fetchAnalytics, 60000);

  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(
      (entries) => { entries.forEach(entry => { if (entry.isIntersecting) { entry.target.style.opacity = '1'; entry.target.style.transform = 'none'; revealObserver.unobserve(entry.target); } }); },
      { rootMargin: '0px 0px -40px 0px', threshold: 0.1 }
    );
    if (timelineList) {
      const mo = new MutationObserver((mutations) => {
        mutations.forEach(m => { m.addedNodes.forEach(node => { if (node.nodeType === 1 && node.classList.contains('timeline-entry')) { node.style.opacity = '0'; node.style.transition = 'opacity 0.4s ease, transform 0.4s ease'; revealObserver.observe(node); } }); });
      });
      mo.observe(timelineList, { childList: true });
    }
  }

})();