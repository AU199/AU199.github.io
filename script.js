const projects = [
    {
        title: "Competition Picker",
        description: "Program that, using FIRST API and STATBotics API, produces a CSV file for each respective competition detailing each team and their performance within a specified time frame.",
        language: "Python",

        url: "https://github.com/AU199/Event-Picker"
    },
    {
        title: "PSA (Carbon Cycle & Deforestation)",
        description: "An animation created entierly using pygame. Animated using a custom engine. (Created on Replit as such is 63% HTML by proportion)",
        language: "Python",
        url: "https://github.com/AU199/PSA_GAME"
    },
];

let currentIndex = 0;
const wheel = document.getElementById('wheel');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const progressIndicator = document.getElementById('progressIndicator');

function getLanguageColor(language) {
    const colors = {
        'JavaScript': '#f1e05a',
        'Python': '#3572A5',
        'Java': '#b07219',
    };
    return colors[language] || '#888';
}

function createProjectCard(project, index) {
    const card = document.createElement('div');
    card.className = 'project-card';
    card.innerHTML = `
                <div class="project-header">
                    <div class="project-icon">${project.title.charAt(0)}</div>
                    <h2 class="project-title">${project.title}</h2>
                </div>
                <p class="project-description">${project.description}</p>
                <div class="project-meta">
                    <div class="meta-item">
                        <svg class="meta-icon" fill="${getLanguageColor(project.language)}" viewBox="0 0 16 16">
                            <circle cx="8" cy="8" r="8"/>
                        </svg>
                        ${project.language}
                    </div>
                </div>
                <a href="${project.url}" target="_blank" rel="noopener noreferrer" class="project-link">
                    View on GitHub
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5z"/>
                        <path d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0v-5z"/>
                    </svg>
                </a>
            `;
    return card;
}

function initializeWheel() {
    projects.forEach((project, index) => {
        const card = createProjectCard(project, index);
        wheel.appendChild(card);
    });
    updateWheel();
    createProgressIndicator();
}

function createProgressIndicator() {
    projects.forEach((_, index) => {
        const dot = document.createElement('div');
        dot.className = 'progress-dot';
        if (index === currentIndex) dot.classList.add('active');
        progressIndicator.appendChild(dot);
    });
}

function updateWheel() {
    const cards = wheel.querySelectorAll('.project-card');
    const totalProjects = projects.length;

    cards.forEach((card, index) => {
        // Remove all classes
        card.classList.remove('active', 'prev', 'next', 'hidden');

        // Calculate previous and next indices
        const prevIndex = (currentIndex - 1 + totalProjects) % totalProjects;
        const nextIndex = (currentIndex + 1) % totalProjects;

        if (index === currentIndex) {
            card.classList.add('active');
        } else if (index === prevIndex) {
            card.classList.add('prev');
            // Add click handler to navigate to previous
            card.onclick = () => prevProject();
        } else if (index === nextIndex) {
            card.classList.add('next');
            // Add click handler to navigate to next
            card.onclick = () => nextProject();
        } else {
            card.classList.add('hidden');
            card.onclick = null;
        }
    });

    const dots = progressIndicator.querySelectorAll('.progress-dot');
    dots.forEach((dot, index) => {
        if (index === currentIndex) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

function nextProject() {
    currentIndex = (currentIndex + 1) % projects.length;
    updateWheel();
}

function prevProject() {
    currentIndex = (currentIndex - 1 + projects.length) % projects.length;
    updateWheel();
}

nextBtn.addEventListener('click', nextProject);
prevBtn.addEventListener('click', prevProject);

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        nextProject();
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        prevProject();
    }
});

initializeWheel();