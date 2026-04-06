/* ============================================================
   NAIK — Naikkan Taraf Hidup Anda
   naik.js — Interactive behaviour for the home page

   CONTENTS
   1. Mobile nav toggle
   2. Stats bar counter animation (triggers on scroll into view)
   ============================================================ */


/* ── 1. MOBILE NAV ───────────────────────────────────────── */

const hamburger  = document.querySelector('.hamburger');
const mobileNav  = document.querySelector('.mobile-nav');

if (hamburger && mobileNav) {
  // Toggle drawer open / closed
  hamburger.addEventListener('click', (e) => {
    e.stopPropagation();
    mobileNav.classList.toggle('open');
  });

  // Close when clicking outside the drawer
  document.addEventListener('click', (e) => {
    if (!mobileNav.contains(e.target) && !hamburger.contains(e.target)) {
      mobileNav.classList.remove('open');
    }
  });

  // Close when any nav link inside the drawer is tapped
  mobileNav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => mobileNav.classList.remove('open'));
  });
}


/* ── 2. STATS BAR COUNTER ANIMATION ─────────────────────── */

/**
 * Animates a number element from 0 to `target`.
 * @param {string} id        - The element's id
 * @param {number} target    - Final value
 * @param {number} duration  - Animation length in ms
 */
function animateCount(id, target, duration = 1800) {
  const el = document.getElementById(id);
  if (!el) return;

  const start = performance.now();

  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    // Ease-out cubic
    const eased    = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(eased * target).toLocaleString();
    if (progress < 1) requestAnimationFrame(step);
  }

  requestAnimationFrame(step);
}

// Only start counting when the stats bar scrolls into view
const statsBar = document.querySelector('.stats-bar');

if (statsBar) {
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      /* ── Update these values to match real data ── */
      animateCount('stat-users',    12400, 1800);
      animateCount('stat-success',  73,    1600);
      animateCount('stat-states',   14,    1200);
      animateCount('stat-earnings', 750,   1800);
      /* ─────────────────────────────────────────── */
      observer.disconnect(); // run once only
    }
  }, { threshold: 0.3 });

  observer.observe(statsBar);
}
