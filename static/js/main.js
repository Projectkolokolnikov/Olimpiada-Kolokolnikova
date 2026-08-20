// ========== ХЕДЕР: СКРОЛЛ ==========
const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
    if (window.scrollY > 30) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// ========== МОБИЛЬНОЕ МЕНЮ ==========
const burger = document.getElementById('burger');
const mobileMenu = document.getElementById('mobileMenu');

if (burger && mobileMenu) {
    burger.addEventListener('click', () => {
        mobileMenu.classList.toggle('open');
        const spans = burger.querySelectorAll('span');
        if (mobileMenu.classList.contains('open')) {
            spans[0].style.transform = 'rotate(45deg) translateY(7px)';
            spans[1].style.opacity = '0';
            spans[2].style.transform = 'rotate(-45deg) translateY(-7px)';
        } else {
            spans[0].style.transform = '';
            spans[1].style.opacity = '';
            spans[2].style.transform = '';
        }
    });

    // Закрыть меню при клике на ссылку
    mobileMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            mobileMenu.classList.remove('open');
            const spans = burger.querySelectorAll('span');
            spans[0].style.transform = '';
            spans[1].style.opacity = '';
            spans[2].style.transform = '';
        });
    });
}

// ========== ПЛАВНАЯ ПРОКРУТКА ==========
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const href = this.getAttribute('href');
        if (href === '#') return;
        const target = document.querySelector(href);
        if (target) {
            e.preventDefault();
            const offset = 80; // высота хедера
            const top = target.getBoundingClientRect().top + window.scrollY - offset;
            window.scrollTo({ top, behavior: 'smooth' });
        }
    });
});

// ========== АККОРДЕОН ТУРОВ ==========
document.querySelectorAll('.stage-card').forEach(card => {
    const header = card.querySelector('.stage-card-header');
    if (!header) return;

    header.addEventListener('click', () => {
        const isActive = card.classList.contains('active');

        // Закрыть все остальные
        document.querySelectorAll('.stage-card').forEach(c => {
            c.classList.remove('active');
        });

        // Открыть текущий если не был открыт
        if (!isActive) {
            card.classList.add('active');
            // Плавная прокрутка к карточке
            setTimeout(() => {
                const offset = 100;
                const top = card.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top, behavior: 'smooth' });
            }, 100);
        }
    });
});

// ========== СОЗДАНИЕ СЛАЙДЕРА ==========
function createSlider(trackId, prevBtnId, nextBtnId, dotsId) {
    const track = document.getElementById(trackId);
    const prevBtn = document.getElementById(prevBtnId);
    const nextBtn = document.getElementById(nextBtnId);
    const dotsContainer = document.getElementById(dotsId);

    if (!track) return;

    const items = track.children;
    const totalItems = items.length;
    let currentIndex = 0;
    let itemsVisible = getItemsVisible();
    let autoplayInterval = null;

    function getItemsVisible() {
        if (window.innerWidth <= 768) return 1;
        if (window.innerWidth <= 1024) return 2;
        return 3;
    }

    function getMaxIndex() {
        return Math.max(0, totalItems - itemsVisible);
    }

    function updateSlider(animate = true) {
        const itemWidth = items[0].offsetWidth + 24; // ширина + gap
        const offset = currentIndex * itemWidth;

        if (!animate) {
            track.style.transition = 'none';
        } else {
            track.style.transition = 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
        }

        track.style.transform = `translateX(-${offset}px)`;
        updateDots();
        updateButtons();
    }

    function updateDots() {
        if (!dotsContainer) return;
        const dots = dotsContainer.querySelectorAll('.slider-dot');
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === currentIndex);
        });
    }

    function updateButtons() {
        if (prevBtn) prevBtn.style.opacity = currentIndex === 0 ? '0.4' : '1';
        if (nextBtn) nextBtn.style.opacity = currentIndex >= getMaxIndex() ? '0.4' : '1';
    }

    // Создание точек
    function createDots() {
        if (!dotsContainer) return;
        dotsContainer.innerHTML = '';
        const dotsCount = getMaxIndex() + 1;
        for (let i = 0; i < dotsCount; i++) {
            const dot = document.createElement('div');
            dot.className = `slider-dot ${i === 0 ? 'active' : ''}`;
            dot.addEventListener('click', () => {
                currentIndex = i;
                updateSlider();
                resetAutoplay();
            });
            dotsContainer.appendChild(dot);
        }
    }

    // Навигация
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                updateSlider();
                resetAutoplay();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentIndex < getMaxIndex()) {
                currentIndex++;
                updateSlider();
                resetAutoplay();
            }
        });
    }

    // Автоплей
    function startAutoplay() {
        autoplayInterval = setInterval(() => {
            if (currentIndex < getMaxIndex()) {
                currentIndex++;
            } else {
                currentIndex = 0;
            }
            updateSlider();
        }, 4000);
    }

    function resetAutoplay() {
        clearInterval(autoplayInterval);
        startAutoplay();
    }

    // Свайп на мобильных
    let touchStartX = 0;
    let touchEndX = 0;

    track.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
    }, { passive: true });

    track.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].clientX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
            if (diff > 0 && currentIndex < getMaxIndex()) {
                currentIndex++;
            } else if (diff < 0 && currentIndex > 0) {
                currentIndex--;
            }
            updateSlider();
        }
    });

    // Адаптив при ресайзе
    window.addEventListener('resize', () => {
        const newVisible = getItemsVisible();
        if (newVisible !== itemsVisible) {
            itemsVisible = newVisible;
            currentIndex = Math.min(currentIndex, getMaxIndex());
            createDots();
            updateSlider(false);
        }
    });

    // Инициализация
    createDots();
    updateSlider(false);
    startAutoplay();

    // Пауза при наведении
    track.parentElement.addEventListener('mouseenter', () => clearInterval(autoplayInterval));
    track.parentElement.addEventListener('mouseleave', startAutoplay);
}

// Запуск слайдеров
createSlider('reviewTrack', 'reviewPrev', 'reviewNext', 'reviewDots');
createSlider('newsTrack', 'newsPrev', 'newsNext', 'newsDots');

// ========== АНИМАЦИИ ПРИ СКРОЛЛЕ ==========
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

document.querySelectorAll(
    '.animate-fade-up, .animate-slide-left, .animate-slide-right'
).forEach(el => observer.observe(el));

// ========== СЧЁТЧИК СТАТИСТИКИ ==========
function animateCounter(el, target, duration = 1500) {
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOut
        const value = Math.round(start + (target - start) * eased);
        el.textContent = value;

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = target + (target > 10 ? '+' : '');
        }
    }

    requestAnimationFrame(update);
}

const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const el = entry.target;
            const target = parseInt(el.getAttribute('data-target'));
            animateCounter(el, target);
            counterObserver.unobserve(el);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-num[data-target]').forEach(el => {
    counterObserver.observe(el);
});

// ========== ЧАСТИЦЫ HERO ==========
function createParticles() {
    const container = document.getElementById('particles');
    if (!container) return;

    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.cssText = `
            left: ${Math.random() * 100}%;
            width: ${Math.random() * 4 + 2}px;
            height: ${Math.random() * 4 + 2}px;
            animation-duration: ${Math.random() * 12 + 8}s;
            animation-delay: ${Math.random() * 8}s;
            opacity: ${Math.random() * 0.5 + 0.1};
        `;
        container.appendChild(particle);
    }
}

createParticles();

// ========== ФОРМА РЕГИСТРАЦИИ: МАСКА ТЕЛЕФОНА ==========
const phoneInput = document.getElementById('phone');
if (phoneInput) {
    phoneInput.addEventListener('input', function() {
        let val = this.value.replace(/\D/g, '');
        if (val.startsWith('7') || val.startsWith('8')) val = val.slice(1);
        let result = '+7';
        if (val.length > 0) result += ' (' + val.slice(0, 3);
        if (val.length >= 3) result += ') ' + val.slice(3, 6);
        if (val.length >= 6) result += '-' + val.slice(6, 8);
        if (val.length >= 8) result += '-' + val.slice(8, 10);
        this.value = result;
    });
}

// ========== ФОРМА РЕГИСТРАЦИИ: МАСКА СНИЛС ==========
const snilsInput = document.getElementById('snils');
if (snilsInput) {
    snilsInput.addEventListener('input', function() {
        let val = this.value.replace(/\D/g, '').slice(0, 11);
        let result = val;
        if (val.length > 3) result = val.slice(0, 3) + '-' + val.slice(3);
        if (val.length > 6) result = val.slice(0, 3) + '-' + val.slice(3, 6) + '-' + val.slice(6);
        if (val.length > 9) result = val.slice(0, 3) + '-' + val.slice(3, 6) + '-' + val.slice(6, 9) + ' ' + val.slice(9);
        this.value = result;
    });
}

// ========== ФОРМА: АНИМАЦИЯ ОТПРАВКИ ==========
const regForm = document.getElementById('regForm');
if (regForm) {
    regForm.addEventListener('submit', function() {
        const btn = document.getElementById('submitBtn');
        if (btn) {
            btn.querySelector('.btn-text').style.display = 'none';
            btn.querySelector('.btn-loader').style.display = 'inline';
            btn.disabled = true;
        }
    });
}

// ========== АКТИВНЫЙ ПУНКТ МЕНЮ ==========
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    let current = '';

    sections.forEach(section => {
        if (window.scrollY >= section.offsetTop - 120) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active-link');
        if (link.getAttribute('href').includes(current)) {
            link.classList.add('active-link');
        }
    });
});