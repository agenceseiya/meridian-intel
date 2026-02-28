/* app.js — MERIDIAN INTEL Dashboard Logic */
(function () {
  'use strict';

  // ============================================================
  // THEME TOGGLE
  // ============================================================
  const root = document.documentElement;
  const toggle = document.querySelector('[data-theme-toggle]');
  const iconMoon = toggle ? toggle.querySelector('.icon-moon') : null;
  const iconSun  = toggle ? toggle.querySelector('.icon-sun')  : null;

  // Default to dark mode always (intelligence platform)
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
    // Flip map background
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

  // ============================================================
  // LIVE CLOCK (IST = UTC+5:30)
  // ============================================================
  const clockEl = document.getElementById('live-clock');
  const dateEl  = document.getElementById('live-date');
  const bannerTS = document.getElementById('banner-timestamp');
  const footerTS = document.getElementById('footer-timestamp');

  const MONTHS = [
    'JAN','FEB','MAR','APR','MAY','JUN',
    'JUL','AUG','SEP','OCT','NOV','DEC'
  ];

  function pad(n) {
    return String(n).padStart(2, '0');
  }

  function getIST() {
    // IST = UTC + 5h30m
    const now    = new Date();
    const utcMs  = now.getTime() + now.getTimezoneOffset() * 60000;
    const istMs  = utcMs + (5 * 60 + 30) * 60000;
    return new Date(istMs);
  }

  function formatTime(d) {
    return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
  }

  function formatDate(d) {
    return pad(d.getDate()) + ' ' + MONTHS[d.getMonth()] + ' ' + d.getFullYear();
  }

  function formatDateTime(d) {
    return formatDate(d) + ' / ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ' IST';
  }

  function tickClock() {
    const ist = getIST();
    if (clockEl) clockEl.textContent = formatTime(ist);
    if (dateEl)  dateEl.textContent  = formatDate(ist);

    const dtStr = formatDateTime(ist);
    if (bannerTS) bannerTS.textContent = dtStr;
    if (footerTS) footerTS.textContent = dtStr;
  }

  // Run immediately then every second
  tickClock();
  setInterval(tickClock, 1000);

  // ============================================================
  // MAP THEME ADAPTATION
  // ============================================================
  function updateMapTheme() {
    const svgMap = document.querySelector('.region-map');
    if (!svgMap) return;
    const bgRect = svgMap.querySelector('rect');
    if (!bgRect) return;
    // Use CSS var value based on current theme
    bgRect.setAttribute('fill', theme === 'dark' ? '#0d1117' : '#f5f5f0');
  }

  // ============================================================
  // MOBILE SIDEBAR TOGGLE
  // ============================================================
  const mobileMenuBtn = document.getElementById('mobile-menu-toggle');
  const sidebar = document.getElementById('sidebar');

  if (mobileMenuBtn && sidebar) {
    mobileMenuBtn.addEventListener('click', () => {
      const isOpen = sidebar.classList.toggle('open');
      mobileMenuBtn.setAttribute('aria-expanded', String(isOpen));
    });
  }

  // ============================================================
  // SCROLL-REVEAL — Timeline entries
  // ============================================================
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'none';
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { rootMargin: '0px 0px -40px 0px', threshold: 0.1 }
    );

    // Apply initial hidden state and observe
    document.querySelectorAll('.timeline-entry').forEach((el, i) => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(4px)';
      el.style.transition = `opacity 0.4s ease ${i * 0.05}s, transform 0.4s ease ${i * 0.05}s`;
      revealObserver.observe(el);
    });
  }

  // ============================================================
  // STATUS INDICATORS — Periodic subtle refresh
  // ============================================================
  // Simulate data freshness by cycling the "last updated" display
  let updateInterval = 0;
  setInterval(() => {
    updateInterval++;
    // Nothing changes content — the clock handles live timestamps
    // Future: hook into a live API for real data
  }, 30000);

})();