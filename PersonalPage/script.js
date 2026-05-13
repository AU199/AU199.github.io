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
let isAnimating = false;

// DOM refs
const mainCard        = document.getElementById('mainCard');
const mainTitle       = document.getElementById('mainTitle');
const mainLink        = document.getElementById('mainLink');
const mainLinkText    = document.getElementById('mainLinkText');
const mainDescription = document.getElementById('mainDescription');
const mainMeta        = document.getElementById('mainMeta');
const prevPanel       = document.getElementById('prevPanel');
const nextPanel       = document.getElementById('nextPanel');
const prevTitle       = document.getElementById('prevTitle');
const nextTitle       = document.getElementById('nextTitle');
const progressIndicator = document.getElementById('progressIndicator');

// ── Build dot indicators ──────────────────────────────────────────────────────
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
    mainTitle.textContent = project.title;

    // Derive a short display URL from the full URL
    const urlObj = (() => { try { return new URL(project.url); } catch { return null; } })();
    const displayLink = urlObj
        ? urlObj.hostname.replace('www.', '') + urlObj.pathname
        : project.url;

    mainLink.href = project.url;
    mainLinkText.textContent = displayLink;

    mainDescription.textContent = project.description;

    // Language badge
    mainMeta.innerHTML = '';
    if (project.language) {
        const badge = document.createElement('span');
        badge.className = 'lang-badge';
        const color = LANG_COLORS[project.language] || '#888';
        badge.innerHTML = `<span class="lang-dot" style="background:${color}"></span>${project.language}`;
        mainMeta.appendChild(badge);
    }
}

function renderSidePanels() {
    const total = projects.length;
    const prevIndex = (currentIndex - 1 + total) % total;
    const nextIndex = (currentIndex + 1) % total;
    prevTitle.textContent = projects[prevIndex].title;
    nextTitle.textContent = projects[nextIndex].title;
}

function render() {
    renderMain(projects[currentIndex]);
    renderSidePanels();
    updateDots();
}

// ── Animated transitions ──────────────────────────────────────────────────────
function animateTransition(direction) {
    if (isAnimating) return false;
    isAnimating = true;

    const outClass = direction === 'next' ? 'slide-out-right' : 'slide-out-left';
    const inClass  = direction === 'next' ? 'slide-in-left'  : 'slide-in-right';

    mainCard.classList.add('animating', outClass);

    setTimeout(() => {
        mainCard.classList.remove('animating', outClass);
        render();
        mainCard.classList.add(inClass);
        setTimeout(() => {
            mainCard.classList.remove(inClass);
            isAnimating = false;
        }, 380);
    }, 200);

    return true;
}

// ── Navigation ────────────────────────────────────────────────────────────────
function nextProject() {
    currentIndex = (currentIndex + 1) % projects.length;
    animateTransition('next');
}

function prevProject() {
    currentIndex = (currentIndex - 1 + projects.length) % projects.length;
    animateTransition('prev');
}

function goTo(index) {
    if (index === currentIndex || isAnimating) return;
    const dir = index > currentIndex ? 'next' : 'prev';
    currentIndex = index;
    animateTransition(dir);
}

// ── Event listeners ───────────────────────────────────────────────────────────
document.getElementById('prevBtn').addEventListener('click', prevProject);
document.getElementById('nextBtn').addEventListener('click', nextProject);
prevPanel.addEventListener('click', prevProject);
nextPanel.addEventListener('click', nextProject);

document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') nextProject();
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   prevProject();
});

// Touch/swipe support
let touchStartX = 0;
document.addEventListener('touchstart', (e) => { touchStartX = e.touches[0].clientX; });
document.addEventListener('touchend',   (e) => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 50) dx < 0 ? nextProject() : prevProject();
});

// ── Init ──────────────────────────────────────────────────────────────────────
buildDots();
mainCard.classList.add('initial-load');
render();
// Remove after it fires once so it never replays on subsequent transitions
mainCard.addEventListener('animationend', () => {
    mainCard.classList.remove('initial-load');
}, { once: true });