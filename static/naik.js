/* ============================================================
   NAIK — Naikkan Taraf Hidup Anda
   naik.js — Interactive behaviour for the home page

   CONTENTS
   1. Mobile nav toggle
   2. Stats bar counter animation (triggers on scroll into view)
   ============================================================ */


/* ── STATS BAR COUNTER ANIMATION ────────────────────────── */

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

/* ═══════════════════════════════════════════
   JOB DATA
═══════════════════════════════════════════ */
const JOBS = [
  {
    id: 1,
    name: "Barista",
    salaryMin: 1400, salaryMax: 2000,
    salaryLabel: "RM 1,400 – 2,000 / mo",
    type: "part-time",
    thumb: "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&q=80",
    tags: ["Café", "Hospitality", "Entry Level"],
    desc: "Brew specialty coffee and create a welcoming café atmosphere for customers.",
    about: "Work in a fast-paced café environment crafting quality beverages. Shifts available mornings, evenings, and weekends — perfect for flexible schedules.",
    duties: "Prepare hot and cold beverages, operate espresso machines, maintain cleanliness, and provide excellent customer service at the counter.",
    reqs: ["No experience needed", "Customer-friendly attitude", "Able to stand for long hours", "Available weekends"],
    perks: ["Meal allowance", "Staff discounts", "EPF & SOCSO", "Training provided"],
    openings: 24, growth: "8%", avgTime: "2 weeks"
  },
  {
    id: 2,
    name: "Grab Driver",
    salaryMin: 2000, salaryMax: 3500,
    salaryLabel: "RM 2,000 – 3,500 / mo",
    type: "freelance",
    thumb: "https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=600&q=80",
    tags: ["Gig", "Flexible Hours", "Own Vehicle"],
    desc: "Drive your own car or motorcycle to deliver passengers or food across your city.",
    about: "Set your own hours and work as much or as little as you want. Many drivers earn above RM 3,000 by peak-hour driving and bonuses.",
    duties: "Pick up and drop off passengers safely, maintain a high rating, complete deliveries on time, and track your earnings via the app.",
    reqs: ["Valid driving licence (B2/D)", "Own vehicle (car or motorcycle)", "Smartphone", "18+ years old"],
    perks: ["Flexible hours", "Weekly payouts", "Incentive bonuses", "No boss"],
    openings: 180, growth: "12%", avgTime: "3 days"
  },
  {
    id: 3,
    name: "Customer Service Rep",
    salaryMin: 1800, salaryMax: 2800,
    salaryLabel: "RM 1,800 – 2,800 / mo",
    type: "full-time",
    thumb: "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=600&q=80",
    tags: ["Office", "Communication", "English"],
    desc: "Assist customers via phone, chat, and email — resolve issues and build loyalty.",
    about: "Join a large BPO or brand directly, handling inbound queries from Malaysian and regional customers. Shift work available.",
    duties: "Answer customer queries, resolve complaints, escalate technical issues, and maintain accurate records in CRM systems.",
    reqs: ["SPM/Diploma", "Good English & Bahasa", "Computer literate", "Patient & empathetic"],
    perks: ["Annual leave", "Medical coverage", "EPF & SOCSO", "Performance bonus"],
    openings: 62, growth: "5%", avgTime: "1 week"
  },
  {
    id: 4,
    name: "Retail Sales Associate",
    salaryMin: 1500, salaryMax: 2200,
    salaryLabel: "RM 1,500 – 2,200 / mo",
    type: "part-time",
    thumb: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=600&q=80",
    tags: ["Retail", "Customer Facing", "Mall"],
    desc: "Help shoppers find the right products and hit sales targets in a retail environment.",
    about: "Work in a branded retail outlet in a shopping mall. Ideal for people who enjoy interacting with customers and have an interest in the product category.",
    duties: "Greet customers, demonstrate products, process transactions, maintain store displays, and assist with inventory.",
    reqs: ["Friendly personality", "Able to work weekends", "Basic numeracy", "SPM preferred"],
    perks: ["Commission bonuses", "Mall discount card", "Uniform provided", "EPF & SOCSO"],
    openings: 47, growth: "4%", avgTime: "1 week"
  },
  {
    id: 5,
    name: "Freelance Graphic Designer",
    salaryMin: 2500, salaryMax: 6000,
    salaryLabel: "RM 2,500 – 6,000 / mo",
    type: "freelance",
    thumb: "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600&q=80",
    tags: ["Creative", "Remote", "Portfolio"],
    desc: "Design logos, social media graphics, and marketing materials for local businesses.",
    about: "Build your own client base or join freelance platforms. Malaysian SMEs are constantly looking for affordable, quality designers.",
    duties: "Create branding assets, social media posts, banners, and print materials. Communicate with clients on revisions and deadlines.",
    reqs: ["Canva / Illustrator / Photoshop", "Portfolio required", "Good communication", "Meets deadlines"],
    perks: ["Work from anywhere", "Set your own rates", "Unlimited earning potential", "Creative freedom"],
    openings: 90, growth: "15%", avgTime: "Immediate"
  },
  {
    id: 6,
    name: "Warehouse Operator",
    salaryMin: 1600, salaryMax: 2400,
    salaryLabel: "RM 1,600 – 2,400 / mo",
    type: "full-time",
    thumb: "https://images.unsplash.com/photo-1553413077-190dd305871c?w=600&q=80",
    tags: ["Physical", "Logistics", "Shift Work"],
    desc: "Sort, pack and organise goods in a modern e-commerce fulfilment warehouse.",
    about: "Work in a structured, team-based environment. Demand has surged with the growth of e-commerce — Shopee and Lazada warehouses are always hiring.",
    duties: "Receive stock, scan items, pick and pack orders, maintain tidiness, and support inventory counts.",
    reqs: ["Physically fit", "Able to do shift work", "Basic literacy", "No experience needed"],
    perks: ["Shift allowance", "OT pay", "EPF & SOCSO", "Free transport provided"],
    openings: 210, growth: "18%", avgTime: "3 days"
  },
  {
    id: 7,
    name: "Online Tutor",
    salaryMin: 1200, salaryMax: 4000,
    salaryLabel: "RM 1,200 – 4,000 / mo",
    type: "remote",
    thumb: "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=600&q=80",
    tags: ["Education", "WFH", "Flexible"],
    desc: "Teach primary or secondary school subjects to students via video call from home.",
    about: "Growing demand for online tuition post-pandemic. Parents prefer home-based learning for their children. You set your hourly rate and schedule.",
    duties: "Plan lessons, conduct live sessions via Zoom/Google Meet, grade work, and communicate with parents on progress.",
    reqs: ["Degree or Diploma in relevant subject", "Stable internet", "Patient & clear communicator", "SPM results (A's preferred)"],
    perks: ["100% work from home", "Flexible scheduling", "Parent referrals grow income", "No commute"],
    openings: 55, growth: "20%", avgTime: "1 week"
  },
  {
    id: 8,
    name: "Food Delivery Rider",
    salaryMin: 1800, salaryMax: 3000,
    salaryLabel: "RM 1,800 – 3,000 / mo",
    type: "freelance",
    thumb: "https://images.unsplash.com/photo-1592861956120-e524fc739696?w=600&q=80",
    tags: ["Gig", "Outdoor", "Motorcycle"],
    desc: "Deliver meals from restaurants to customers using GrabFood, FoodPanda, or Beep.",
    about: "One of the easiest ways to earn immediately. Register online and start taking orders the same week. Peak hours on weekday lunches and weekends pay highest.",
    duties: "Accept delivery orders, pick up meals from restaurants, deliver to customers, and maintain high ratings.",
    reqs: ["Motorcycle licence (B2)", "Own motorcycle", "Smartphone", "Physical fitness"],
    perks: ["Daily/weekly payouts", "Bonus incentives", "Set your own hours", "No interview needed"],
    openings: 300, growth: "10%", avgTime: "2 days"
  },
  {
    id: 9,
    name: "Admin / Clerk",
    salaryMin: 1700, salaryMax: 2500,
    salaryLabel: "RM 1,700 – 2,500 / mo",
    type: "full-time",
    thumb: "https://images.unsplash.com/photo-1497032628192-86f99bcd76bc?w=600&q=80",
    tags: ["Office", "Documentation", "Entry Level"],
    desc: "Handle filing, data entry, scheduling and correspondence in a professional office.",
    about: "A reliable office role with regular hours and a clear career path. Ideal for those with SPM or Diploma who are organised and detail-oriented.",
    duties: "Manage documents, update spreadsheets, respond to emails, coordinate meetings, and support department heads.",
    reqs: ["SPM / Diploma", "MS Office proficient", "Good Bahasa & English", "Organised & punctual"],
    perks: ["Fixed hours (Mon–Fri)", "Annual leave", "Medical benefit", "Career advancement"],
    openings: 39, growth: "3%", avgTime: "2 weeks"
  },
  {
    id: 10,
    name: "Social Media Manager",
    salaryMin: 2500, salaryMax: 5000,
    salaryLabel: "RM 2,500 – 5,000 / mo",
    type: "remote",
    thumb: "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=600&q=80",
    tags: ["Digital", "Creative", "WFH"],
    desc: "Grow brands on Instagram, TikTok, and Facebook through engaging content strategies.",
    about: "Businesses of all sizes are investing in social media. Many companies hire part-remote or fully remote social media managers to run their online presence.",
    duties: "Plan and schedule content, engage with followers, analyse performance metrics, run paid ads, and report monthly results.",
    reqs: ["Experience with IG/TikTok", "Basic graphic/video editing", "Copywriting skills", "Analytical mindset"],
    perks: ["Fully remote option", "Creative work", "Performance bonuses", "Portfolio building"],
    openings: 41, growth: "22%", avgTime: "1–2 weeks"
  },
  {
    id: 11,
    name: "Healthcare Aide",
    salaryMin: 1600, salaryMax: 2600,
    salaryLabel: "RM 1,600 – 2,600 / mo",
    type: "full-time",
    thumb: "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&q=80",
    tags: ["Care", "Hospital", "Meaningful"],
    desc: "Support nurses and doctors by assisting patients with daily care needs in hospitals or clinics.",
    about: "A deeply meaningful role with growing demand as Malaysia's healthcare sector expands. On-the-job training is commonly provided.",
    duties: "Assist patients with personal hygiene, mobility support, meal service, vital sign monitoring, and ward maintenance.",
    reqs: ["SPM minimum", "Compassionate & patient", "Physical stamina", "Able to do shift work"],
    perks: ["Shift allowance", "EPF & SOCSO", "Training provided", "Job security"],
    openings: 88, growth: "14%", avgTime: "1 week"
  },
  {
    id: 12,
    name: "Home Baker / Pastry Seller",
    salaryMin: 800, salaryMax: 3500,
    salaryLabel: "RM 800 – 3,500 / mo",
    type: "freelance",
    thumb: "https://images.unsplash.com/photo-1556217477-d325251ece38?w=600&q=80",
    tags: ["Home-based", "For Her", "Micro-business"],
    desc: "Start your own home bakery and sell cakes, cookies, and kuih via WhatsApp and Shopee.",
    about: "One of the most popular income streams for Malaysian mothers. Low start-up cost, flexible hours, and you can grow at your own pace using social media.",
    duties: "Bake and decorate products, manage orders via WhatsApp, package goods, handle deliveries or arrange pick-up, and market on Instagram.",
    reqs: ["Passion for baking", "Basic food hygiene knowledge", "Smartphone for orders", "Small initial investment"],
    perks: ["Work from home", "Set your own hours", "Family-friendly schedule", "Unlimited growth potential"],
    openings: 0, growth: "25%", avgTime: "Immediate"
  }
];

/* ═══════════════════════════════════════════
   STATE
═══════════════════════════════════════════ */
let savedIds = new Set(JSON.parse(localStorage.getItem('naik_saved') || '[]'));
let savedOrder = JSON.parse(localStorage.getItem('naik_saved_order') || '[]');
let activeFilter = 'all';
let activeSort = 'default';
let rankingMode = false;
let currentJob = null;
let dragSrcId = null;

/* ═══════════════════════════════════════════
   HELPERS
═══════════════════════════════════════════ */
function persist() {
  localStorage.setItem('naik_saved', JSON.stringify([...savedIds]));
  localStorage.setItem('naik_saved_order', JSON.stringify(savedOrder));
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 2200);
}

function updateBadge() {
    const badge = document.getElementById('saved-badge'); // (Keep whatever ID you currently have)
    
    // THE FIX: If the badge doesn't exist, stop running this function!
    if (!badge) return; 
    
    badge.textContent = savedIds.size; 
}

function salaryBracket(job) {
  if (job.salaryMax < 2000) return 'salary-low';
  if (job.salaryMin >= 4000) return 'salary-high';
  return 'salary-mid';
}

/* ═══════════════════════════════════════════
   CARD BUILDER
═══════════════════════════════════════════ */
function buildCard(job, inSaved = false) {
  const isSaved = savedIds.has(job.id);
  const card = document.createElement('div');
  card.className = 'job-card';
  card.dataset.id = job.id;
  card.dataset.type = job.type;
  card.dataset.salaryBracket = salaryBracket(job);
  card.dataset.salaryMin = job.salaryMin;
  card.dataset.name = job.name;
  card.draggable = false; // set in ranking mode

  card.innerHTML = `
    <div class="job-thumb" style="background-image:url('${job.thumb}')"></div>
    <div class="job-gradient"></div>
    <span class="job-type-badge ${job.type}">${job.type.replace('-', ' ')}</span>
    <div class="rank-number">—</div>
    <button class="heart-btn${isSaved ? ' saved' : ''}" aria-label="Save job" data-id="${job.id}">
      <svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
    </button>
    <div class="job-info">
      <div class="job-name">${job.name}</div>
      <div class="job-salary">${job.salaryLabel}</div>
    </div>
    <div class="job-desc">
      <span class="desc-label">${job.type.replace('-', ' ')}</span>
      <div class="desc-title">${job.name}</div>
      <div class="desc-salary">${job.salaryLabel}</div>
      <div class="desc-text">${job.desc}</div>
      <div class="desc-tags">${job.tags.map(t => `<span class="desc-tag">${t}</span>`).join('')}</div>
      <span class="desc-cta">View Details →</span>
    </div>
  `;

  // Heart
  card.querySelector('.heart-btn')?.addEventListener('click', e => {
    e.stopPropagation();
    toggleSave(job.id, card.querySelector('.heart-btn'));
  });

  // Click card → open modal
  card?.addEventListener('click', (e) => {
    if (rankingMode) return;
    openModal(job);
  });

  return card;
}

/* ═══════════════════════════════════════════
   EXPLORE GRID
═══════════════════════════════════════════ */
function filteredJobs() {
  let jobs = [...JOBS];

  if (activeFilter === 'all') { /* no filter */ }
  else if (['full-time','part-time','freelance','remote'].includes(activeFilter)) {
    jobs = jobs.filter(j => j.type === activeFilter);
  } else {
    jobs = jobs.filter(j => salaryBracket(j) === activeFilter);
  }

  if (activeSort === 'salary-asc') jobs.sort((a,b) => a.salaryMin - b.salaryMin);
  else if (activeSort === 'salary-desc') jobs.sort((a,b) => b.salaryMin - a.salaryMin);
  else if (activeSort === 'name-asc') jobs.sort((a,b) => a.name.localeCompare(b.name));

  return jobs;
}

function renderExplore() {
  const grid = document.getElementById('explore-grid');
  
  // 1. THE FIX: If the grid doesn't exist, we aren't on the Explore page. Stop running!
  if (!grid) return; 
  
  grid.innerHTML = '';
  const jobs = filteredJobs();
  
  // 2. EXTRA SAFETY: Only update the results number if that element actually exists
  const resultsNum = document.getElementById('results-num');
  if (resultsNum) {
      resultsNum.textContent = jobs.length;
  }
  
  jobs.forEach(j => grid.appendChild(buildCard(j, false)));
}

/* ═══════════════════════════════════════════
   SAVED GRID
═══════════════════════════════════════════ */
function savedJobs() {
  // Maintain order
  const ordered = savedOrder.filter(id => savedIds.has(id));
  const newIds = [...savedIds].filter(id => !savedOrder.includes(id));
  savedOrder = [...ordered, ...newIds];
  persist();
  return savedOrder.map(id => JOBS.find(j => j.id === id)).filter(Boolean);
}

function renderSaved() {
  const grid = document.getElementById('saved-grid');
  grid.innerHTML = '';
  const jobs = savedJobs();
  if (jobs.length === 0) {
    grid.innerHTML = `<div class="empty-state">
      <div class="emoji">🤍</div>
      <h3>No saved jobs yet</h3>
      <p>Heart any job in Explore to save it here.</p>
    </div>`;
    return;
  }
  jobs.forEach((j, i) => {
    const card = buildCard(j, true);
    const rankNum = card.querySelector('.rank-number');
    rankNum.textContent = i + 1;
    if (rankingMode) {
      card.draggable = true;
      attachDragEvents(card);
    }
    grid.appendChild(card);
  });
  if (rankingMode) grid.classList.add('ranking-mode');
  else grid.classList.remove('ranking-mode');
}

/* ═══════════════════════════════════════════
   SAVE / UNSAVE
═══════════════════════════════════════════ */
function toggleSave(id, btn) {
  if (savedIds.has(id)) {
    savedIds.delete(id);
    savedOrder = savedOrder.filter(x => x !== id);
    btn.classList.remove('saved');
    showToast('Removed from saved');
  } else {
    savedIds.add(id);
    savedOrder.push(id);
    btn.classList.add('saved');
    showToast('💾 Job saved!');
  }
  persist();
  updateBadge();
  // Sync heart buttons across both grids
  document.querySelectorAll(`.heart-btn[data-id="${id}"]`).forEach(b => {
    if (savedIds.has(id)) b.classList.add('saved');
    else b.classList.remove('saved');
  });
  if (document.getElementById('tab-saved').style.display !== 'none') renderSaved();
}

/* ═══════════════════════════════════════════
   DRAG-TO-RANK
═══════════════════════════════════════════ */
function attachDragEvents(card) {
  card?.addEventListener('dragstart', e => {
    dragSrcId = parseInt(card.dataset.id);
    card.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
  });
  card?.addEventListener('dragend', () => {
    card.classList.remove('dragging');
    document.querySelectorAll('.job-card').forEach(c => c.classList.remove('drag-over'));
  });
  card?.addEventListener('dragover', e => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    document.querySelectorAll('.job-card').forEach(c => c.classList.remove('drag-over'));
    card.classList.add('drag-over');
  });
  card?.addEventListener('drop', e => {
    e.preventDefault();
    const destId = parseInt(card.dataset.id);
    if (dragSrcId === destId) return;
    const srcIdx = savedOrder.indexOf(dragSrcId);
    const destIdx = savedOrder.indexOf(destId);
    savedOrder.splice(srcIdx, 1);
    savedOrder.splice(destIdx, 0, dragSrcId);
    persist();
    renderSaved();
    showToast('✓ Order saved');
  });
}

/* ═══════════════════════════════════════════
   MODAL
═══════════════════════════════════════════ */
function openModal(job) {
  currentJob = job;
  document.getElementById('modal-hero').style.backgroundImage = `url('${job.thumb}')`;
  document.getElementById('modal-title').textContent = job.name;
  document.getElementById('modal-salary').textContent = job.salaryLabel;
  document.getElementById('modal-about').textContent = job.about;
  document.getElementById('modal-duties').textContent = job.duties;
  document.getElementById('modal-reqs').innerHTML = job.reqs.map(r => `<span class="modal-pill">${r}</span>`).join('');
  document.getElementById('modal-perks').innerHTML = job.perks.map(p => `<span class="modal-pill" style="background:var(--teal-lt); border-color:var(--teal)">${p}</span>`).join('');
  document.getElementById('modal-stats').innerHTML = `
    <div class="modal-stat"><span class="n">${job.openings || '—'}</span><span class="d">Open positions</span></div>
    <div class="modal-stat"><span class="n">${job.growth}</span><span class="d">Job growth</span></div>
    <div class="modal-stat"><span class="n">${job.avgTime}</span><span class="d">Time to hire</span></div>
  `;
  updateModalSaveBtn();
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function updateModalSaveBtn() {
  if (!currentJob) return;
  const btn = document.getElementById('modal-save-btn');
  btn.textContent = savedIds.has(currentJob.id) ? '💛 Saved' : '🤍 Save Job';
}

document.getElementById('modal-close')?.addEventListener('click', closeModal);
document.getElementById('modal-overlay')?.addEventListener('click', e => {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
});
document.getElementById('modal-save-btn')?.addEventListener('click', () => {
  if (!currentJob) return;
  toggleSave(currentJob.id, { classList: { add(){}, remove(){}, has:()=>false } });
  updateModalSaveBtn();
});
/* ═══════════════════════════════════════════
   TABS
═══════════════════════════════════════════ */
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn?.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.dataset.tab;
    document.getElementById('tab-explore').style.display = tab === 'explore' ? '' : 'none';
    document.getElementById('tab-saved').style.display = tab === 'saved' ? '' : 'none';
    if (tab === 'saved') renderSaved();
  });
});

/* ═══════════════════════════════════════════
   FILTERS
═══════════════════════════════════════════ */
document.querySelectorAll('.filter-chip').forEach(chip => {
  chip?.addEventListener('click', () => {
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeFilter = chip.dataset.filter;
    renderExplore();
  });
});
document.getElementById('sort-select')?.addEventListener('change', e => {
  activeSort = e.target.value;
  renderExplore();
});

/* ═══════════════════════════════════════════
   RANKING MODE TOGGLE
═══════════════════════════════════════════ */
document.getElementById('rank-toggle')?.addEventListener('click', () => {
  rankingMode = !rankingMode;
  document.getElementById('rank-toggle').classList.toggle('active', rankingMode);
  document.getElementById('rank-hint').classList.toggle('hidden', !rankingMode);
  renderSaved();
});

/* ═══════════════════════════════════════════
   INIT
═══════════════════════════════════════════ */
updateBadge();
renderExplore();

/* ── HERO BATIK SPOTLIGHT ────────────────────────────────── */
(function () {
  const mount = document.getElementById('batik-mount');
  if (!mount) return;

  const svgUrl = mount.dataset.svgUrl;
  if (!svgUrl) return;

  fetch(svgUrl)
    .then(r => {
      if (!r.ok) throw new Error('SVG fetch failed: ' + r.status);
      return r.text();
    })
    .then(svgText => {
      mount.innerHTML = svgText;

      const hero   = document.querySelector('.hero');
      const svg    = mount.querySelector('svg');
      const circle = mount.querySelector('#spotlight-circle');
      if (!hero || !svg || !circle) return;

      hero.addEventListener('mousemove', (e) => {
        if (window.innerWidth <= 768) return;
        const rect = hero.getBoundingClientRect();
        circle.setAttribute('cx', e.clientX - rect.left);
        circle.setAttribute('cy', e.clientY - rect.top);
        svg.style.opacity = '1';
      });

      hero.addEventListener('mouseleave', () => {
        if (window.innerWidth <= 768) return;
        svg.style.opacity = '0';
        setTimeout(() => {
          circle.setAttribute('cx', -999);
          circle.setAttribute('cy', -999);
        }, 400);
      });
    })
    .catch(err => console.warn('Batik load error:', err));
})();