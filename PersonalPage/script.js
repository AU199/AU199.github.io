const projects = [
    {
        title: "Competition Picker",
        description: "Program that, using FIRST API and STATBotics API, produces a CSV file for each respective competition detailing each team and their performance within a specified time frame.",
        language: "Python",
        url: "https://github.com/AU199/Competition-Picker"
    },
    {
        title: "PSA Animation",
        description: "An animation created entirely using pygame. Animated using a custom engine. (Created on Replit — 63% HTML by file proportion.)",
        language: "Python",
        url: "https://github.com/AU199/PSA_GAME"
    },
    {
        title: "Personal Website",
        description: "Created to showcase and give links to my personal projects. Built with the help of AI tools.",
        language: "HTML",
        url: "https://github.com/AU199/AU199.github.io"
    },
    {
        title: "Swim-Team Data Collector",
        description: "Made for the swim coach to gain insight into times and other data about their swimmers. Taught me web scraping and data processing skills.",
        language: "Python",
        url: "https://github.com/AU199/Swim-Team-Webscraper"
    },
    {
        title: "Image Recreation Using the Fourier Transform",
        description: "This is a project I created that uses OpenCV2 in order to find contours in images, after which it uses the contours as a signal function and finds the solutions for the number of epicucles already pre-programmed. I learnt how to use cv2, numpy and matplotlib",
        language: "Python",
        url: "https://github.com/AU199/Image-Recreation"
    },
    {
        title: "Face Recognizer",
        description: "Using OpenCV2 and PyTorch, this can recogize getures either on the face or something bigger, leading to different images showing up in a pygame window.",
        language:"Python",
        url: "https://github.com/AU199/Emotion-Recognizer"
    },
    {
        title: "Chess Engine",
        description: "Though this chess engine plays at a 400 elo level, it taught me many valuable skills pertaining to machine learning, alpha-beta pruning, and program optimization.",
        language: "Python",
        url: "https://github.com/AU199/NN-Alpha-Beta-Pruning"
    },
    {
        title: "Mechanical Keyboard",
        description: "My introduction to KiCad — creating schematics, routing PCBs, building a bill of materials, and minimizing costs. Created through Hack Club's Blueprint program.",
        language: "",
        url: "https://github.com/AU199/Mecahnical_Keyboard.git"
    }
];

const LANG_COLORS = {
    'Python': '#3572A5',
    'Java':   '#b07219',
    'HTML':   '#ce331b',
    '':       null
};

let currentIndex = 0;
let isAnimating  = false;

// ── DOM refs ──────────────────────────────────────────────────────────────────
const mainCard          = document.getElementById('mainCard');
const mainTitle         = document.getElementById('mainTitle');
const mainLink          = document.getElementById('mainLink');
const mainLinkText      = document.getElementById('mainLinkText');
const mainDescription   = document.getElementById('mainDescription');
const mainMeta          = document.getElementById('mainMeta');
const prevPanel         = document.getElementById('prevPanel');
const nextPanel         = document.getElementById('nextPanel');
const prevTitle         = document.getElementById('prevTitle');
const nextTitle         = document.getElementById('nextTitle');
const progressIndicator = document.getElementById('progressIndicator');

// Overlay refs
const detailOverlay     = document.getElementById('detailOverlay');
const detailTitle       = document.getElementById('detailTitle');
const detailDescription = document.getElementById('detailDescription');
const detailMeta        = document.getElementById('detailMeta');
const detailLink        = document.getElementById('detailLink');

// ── Helpers ───────────────────────────────────────────────────────────────────
function makeLangBadge(language) {
    if (!language) return null;
    const badge = document.createElement('span');
    badge.className = 'lang-badge';
    const color = LANG_COLORS[language] || '#888';
    badge.innerHTML = `<span class="lang-dot" style="background:${color}"></span>${language}`;
    return badge;
}

function shortUrl(url) {
    try {
        const u = new URL(url);
        return u.hostname.replace('www.', '') + u.pathname;
    } catch { return url; }
}

// ── Dot indicators ────────────────────────────────────────────────────────────
function buildDots() {
    progressIndicator.innerHTML = '';
    projects.forEach((_, i) => {
        const dot = document.createElement('button');
        dot.className = 'nav__dot' + (i === currentIndex ? ' active' : '');
        dot.setAttribute('aria-label', `Go to project ${i + 1}`);
        dot.addEventListener('click', () => goTo(i));
        progressIndicator.appendChild(dot);
    });
}

function updateDots() {
    progressIndicator.querySelectorAll('.nav__dot').forEach((dot, i) => {
        dot.classList.toggle('active', i === currentIndex);
    });
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderMain(project) {
    mainTitle.textContent    = project.title;
    mainLink.href            = project.url;
    mainLinkText.textContent = shortUrl(project.url);
    mainDescription.textContent = project.description;

    mainMeta.innerHTML = '';
    const badge = makeLangBadge(project.language);
    if (badge) mainMeta.appendChild(badge);
}

function renderSidePanels() {
    const total    = projects.length;
    const prevIdx  = (currentIndex - 1 + total) % total;
    const nextIdx  = (currentIndex + 1) % total;
    prevTitle.textContent = projects[prevIdx].title;
    nextTitle.textContent = projects[nextIdx].title;
}

function render() {
    renderMain(projects[currentIndex]);
    renderSidePanels();
    updateDots();
}

// ── Mobile detail overlay ─────────────────────────────────────────────────────
function openDetail() {
    const project = projects[currentIndex];
    detailTitle.textContent       = project.title;
    detailDescription.textContent = project.description;
    detailLink.href               = project.url;

    detailMeta.innerHTML = '';
    const badge = makeLangBadge(project.language);
    if (badge) detailMeta.appendChild(badge);

    detailOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeDetail() {
    detailOverlay.classList.remove('open');
    document.body.style.overflow = '';
}

// Tap the dim backdrop to close
detailOverlay.addEventListener('click', (e) => {
    if (e.target === detailOverlay) closeDetail();
});

// Swipe down on sheet to close
let sheetTouchStartY = 0;
const detailSheet = document.getElementById('detailSheet');

// FIX 2: Use { passive: false } and stopPropagation so the expand button tap
// doesn't also get swallowed by the document-level swipe handler.
const mobileExpandBtn = document.getElementById('mobileExpandBtn');
mobileExpandBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    openDetail();
});
// Also handle touchend on the button so iOS tap-delay isn't an issue
mobileExpandBtn.addEventListener('touchend', (e) => {
    e.preventDefault();   // prevents ghost click + stops swipe handler from firing
    e.stopPropagation();
    openDetail();
});

detailSheet.addEventListener('touchstart', (e) => {
    sheetTouchStartY = e.touches[0].clientY;
}, { passive: true });
detailSheet.addEventListener('touchend', (e) => {
    const dy = e.changedTouches[0].clientY - sheetTouchStartY;
    if (dy > 60) closeDetail();
});

// ── Animated transitions ──────────────────────────────────────────────────────
function animateTransition(direction) {
    if (isAnimating) return;
    isAnimating = true;

    const outClass = direction === 'next' ? 'slide-out-right' : 'slide-out-left';
    const inClass  = direction === 'next' ? 'slide-in-left'   : 'slide-in-right';

    mainCard.classList.add(outClass);

    setTimeout(() => {
        mainCard.classList.remove(outClass);
        render();
        mainCard.classList.add(inClass);
        setTimeout(() => {
            mainCard.classList.remove(inClass);
            isAnimating = false;
        }, 380);
    }, 200);
}

// ── Navigation ────────────────────────────────────────────────────────────────
function nextProject() {
    closeDetail();
    currentIndex = (currentIndex + 1) % projects.length;
    animateTransition('next');
}

function prevProject() {
    closeDetail();
    currentIndex = (currentIndex - 1 + projects.length) % projects.length;
    animateTransition('prev');
}

// FIX 1: goTo computes wrap-aware direction so clicking a dot or side panel
// never produces a double-step. We also guard against firing while animating.
function goTo(index) {
    if (index === currentIndex || isAnimating) return;
    closeDetail();

    // Determine shortest-path direction, accounting for wrap-around
    const total = projects.length;
    const fwdDist = (index - currentIndex + total) % total;
    const dir = fwdDist <= total / 2 ? 'next' : 'prev';

    currentIndex = index;
    animateTransition(dir);
}

// ── Event listeners ───────────────────────────────────────────────────────────
document.getElementById('prevBtn').addEventListener('click', prevProject);
document.getElementById('nextBtn').addEventListener('click', nextProject);

// FIX 1 (continued): side panels call goTo with the adjacent index rather than
// prevProject/nextProject directly, so a single click can never decrement twice.
prevPanel.addEventListener('click', () => {
    const idx = (currentIndex - 1 + projects.length) % projects.length;
    goTo(idx);
});
nextPanel.addEventListener('click', () => {
    const idx = (currentIndex + 1) % projects.length;
    goTo(idx);
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape')                               closeDetail();
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown')  nextProject();
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')    prevProject();
});

// Horizontal swipe on main area to navigate (but not inside the sheet)
let touchStartX = 0;
let touchStartY = 0;
document.addEventListener('touchstart', (e) => {
    if (!detailOverlay.classList.contains('open')) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    }
}, { passive: true });
document.addEventListener('touchend', (e) => {
    if (detailOverlay.classList.contains('open')) return;
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;
    // Only treat as a horizontal swipe if it's clearly more horizontal than vertical
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        dx < 0 ? nextProject() : prevProject();
    }
}, { passive: true });

// ── Init ──────────────────────────────────────────────────────────────────────
buildDots();
mainCard.classList.add('initial-load');
render();
mainCard.addEventListener('animationend', () => {
    mainCard.classList.remove('initial-load');
}, { once: true });