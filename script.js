// ============================================
// THEME TOGGLE
// ============================================
const themeToggle = document.getElementById('themeToggle');
const html = document.documentElement;

// Load saved theme or default to light
const savedTheme = localStorage.getItem('theme') || 'light';
html.setAttribute('data-theme', savedTheme);

themeToggle.addEventListener('click', () => {
    const current = html.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
});

// ============================================
// NAVBAR SCROLL EFFECT
// ============================================
const navbar = document.getElementById('navbar');
const backToTop = document.getElementById('backToTop');

window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;

    // Navbar shadow
    navbar.classList.toggle('scrolled', scrollY > 50);

    // Back to top button
    backToTop.classList.toggle('visible', scrollY > 500);

    // Active nav link
    updateActiveNav();
});

// ============================================
// ACTIVE NAV LINK HIGHLIGHTER
// ============================================
function updateActiveNav() {
    const sections = document.querySelectorAll('.section, .hero');
    const navLinks = document.querySelectorAll('.nav-links a');
    let current = '';

    sections.forEach(section => {
        const sectionTop = section.offsetTop - 100;
        if (window.scrollY >= sectionTop) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
            link.classList.add('active');
        }
    });
}

// ============================================
// MOBILE NAVIGATION
// ============================================
const navHamburger = document.getElementById('navHamburger');
const navLinks = document.getElementById('navLinks');

navHamburger.addEventListener('click', () => {
    navHamburger.classList.toggle('active');
    navLinks.classList.toggle('active');
});

// Close mobile nav on link click
navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
        navHamburger.classList.remove('active');
        navLinks.classList.remove('active');
    });
});

// ============================================
// BACK TO TOP
// ============================================
backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ============================================
// TYPING EFFECT
// ============================================
const typedElement = document.getElementById('typed');
const words = [
    'Structural Engineering',
    'Aerospace Engineering',
    'Structural Health Monitoring',
    'Composite Materials'
];
let wordIndex = 0;
let charIndex = 0;
let isDeleting = false;
let typeSpeed = 100;

function typeEffect() {
    const currentWord = words[wordIndex];

    if (isDeleting) {
        typedElement.textContent = currentWord.substring(0, charIndex - 1);
        charIndex--;
        typeSpeed = 50;
    } else {
        typedElement.textContent = currentWord.substring(0, charIndex + 1);
        charIndex++;
        typeSpeed = 100;
    }

    if (!isDeleting && charIndex === currentWord.length) {
        typeSpeed = 2000; // pause at end
        isDeleting = true;
    } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        wordIndex = (wordIndex + 1) % words.length;
        typeSpeed = 500;
    }

    setTimeout(typeEffect, typeSpeed);
}

typeEffect();

// ============================================
// ANIMATED COUNTERS
// ============================================
function animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    counters.forEach(counter => {
        const target = parseFloat(counter.getAttribute('data-target'));
        const isDecimal = target % 1 !== 0;
        const duration = 2000;
        const steps = 60;
        const increment = target / steps;
        let current = 0;
        let step = 0;

        const timer = setInterval(() => {
            step++;
            current += increment;
            if (step >= steps) {
                current = target;
                clearInterval(timer);
            }
            counter.textContent = isDecimal ? current.toFixed(1) : Math.round(current);
        }, duration / steps);
    });
}

// Run counters when hero is visible
const heroObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounters();
            heroObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.3 });

heroObserver.observe(document.getElementById('hero'));

// ============================================
// SCROLL REVEAL ANIMATIONS
// ============================================
function setupScrollReveal() {
    const revealElements = document.querySelectorAll(
        '.about-grid, .timeline-item, ' +
        '.course-card, .project-card, .teaching-card, ' +
        '.contact-grid'
    );

    revealElements.forEach(el => el.classList.add('reveal'));

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    revealElements.forEach(el => revealObserver.observe(el));
}

setupScrollReveal();

// ============================================
// COURSE FILTER
// ============================================
const filterBtns = document.querySelectorAll('.filter-btn');
const courseCards = document.querySelectorAll('.course-card');

filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Update active button
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.getAttribute('data-filter');

        courseCards.forEach(card => {
            if (filter === 'all' || card.getAttribute('data-category') === filter) {
                card.classList.remove('hidden');
                card.style.animation = 'fadeIn 0.4s ease';
            } else {
                card.classList.add('hidden');
            }
        });
    });
});

// ============================================
// PARTICLES (Hero background)
// ============================================
function createParticles() {
    const container = document.getElementById('particles');
    const count = 30;

    for (let i = 0; i < count; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const size = Math.random() * 6 + 2;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 6 + 's';
        particle.style.animationDuration = (Math.random() * 4 + 4) + 's';
        container.appendChild(particle);
    }
}

createParticles();

// ============================================
// CONTACT FORM (Basic handler)
// ============================================
const contactForm = document.getElementById('contactForm');

contactForm.addEventListener('submit', (e) => {
    e.preventDefault();

    // Get form data
    const formData = new FormData(contactForm);
    const name = formData.get('name');
    const email = formData.get('email');
    const subject = formData.get('subject');
    const message = formData.get('message');

    // Create mailto link as fallback
    const mailtoLink = `mailto:your.email@university.edu?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(`From: ${name} (${email})\n\n${message}`)}`;
    window.location.href = mailtoLink;

    // Show success feedback
    const btn = contactForm.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '✓ Opening Email Client...';
    btn.style.background = '#22c55e';

    setTimeout(() => {
        btn.innerHTML = originalText;
        btn.style.background = '';
        contactForm.reset();
    }, 3000);
});

// ============================================
// SMOOTH SCROLL for anchor links
// ============================================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// ============================================
// FADE IN ANIMATION KEYFRAME (CSS-in-JS)
// ============================================
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

// ============================================
// CONSOLE EASTER EGG
// ============================================
console.log('%c👋 Hello there!', 'font-size: 24px; font-weight: bold;');
console.log('%cThanks for checking out my source code!', 'font-size: 14px; color: #818cf8;');
console.log('%cFeel free to reach out if you want to collaborate.', 'font-size: 12px; color: #888;');
