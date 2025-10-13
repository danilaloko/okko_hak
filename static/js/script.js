/* ==============================
   Okko Discovery - Новая концепция
   Интерактивная платформа рекомендаций
   ============================== */

// Глобальные переменные
let currentContent = null;
let likedCount = 0;
let dislikedCount = 0;
let isAnimating = false;
let userPreferences = {
    categories: [],
    genres: [],
    ratings: []
};

// Данные для демонстрации
const categories = [
    { id: 'movies', title: 'Фильмы', icon: 'fas fa-film', description: 'Художественные фильмы' },
    { id: 'series', title: 'Сериалы', icon: 'fas fa-tv', description: 'Многосерийные проекты' },
    { id: 'documentaries', title: 'Документальные', icon: 'fas fa-book', description: 'Познавательный контент' },
    { id: 'cartoons', title: 'Мультфильмы', icon: 'fas fa-magic', description: 'Анимационные фильмы' }
];

const sampleContent = [
    {
        id: 1,
        title: 'Интерстеллар',
        description: 'Эпическая космическая драма о путешествии через червоточину',
        poster: 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=400&h=600&fit=crop',
        rating: 8.6,
        year: 2014,
        genre: 'Фантастика'
    },
    {
        id: 2,
        title: 'Дюна',
        description: 'Эпическая фантастическая сага о пустынной планете Арракис',
        poster: 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop',
        rating: 8.0,
        year: 2021,
        genre: 'Фантастика'
    },
    {
        id: 3,
        title: 'Топ Ган: Мэверик',
        description: 'Продолжение культового фильма о пилотах-истребителях',
        poster: 'https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=400&h=600&fit=crop',
        rating: 8.3,
        year: 2022,
        genre: 'Боевик'
    },
    {
        id: 4,
        title: 'Оппенгеймер',
        description: 'Биографическая драма о создателе атомной бомбы',
        poster: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=600&fit=crop',
        rating: 8.5,
        year: 2023,
        genre: 'Драма'
    },
    {
        id: 5,
        title: 'Барби',
        description: 'Комедийная фантазия о кукле Барби в реальном мире',
        poster: 'https://images.unsplash.com/photo-1594736797933-d0c4a4a0b8a0?w=400&h=600&fit=crop',
        rating: 7.0,
        year: 2023,
        genre: 'Комедия'
    }
];

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Основная инициализация
async function initializeApp() {
    hideLoadingScreen();
    setupEventListeners();
    loadCategories();
    loadRecommendations();
    loadInteractiveContent();
    updateStats();
}

// Скрытие загрузочного экрана
function hideLoadingScreen() {
    setTimeout(() => {
        const loadingScreen = document.getElementById('loadingScreen');
        loadingScreen.classList.add('hidden');
    }, 1500);
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Кнопки управления
    document.getElementById('likeBtn').addEventListener('click', () => handleInteraction('like'));
    document.getElementById('dislikeBtn').addEventListener('click', () => handleInteraction('dislike'));
    
    // Кнопка обновления
    document.getElementById('refreshBtn').addEventListener('click', loadRecommendations);
    
    // Кнопки завершения
    document.getElementById('viewRecommendations').addEventListener('click', showRecommendations);
    document.getElementById('restartAnalysis').addEventListener('click', restartAnalysis);
    
    // Touch события для карточек
    setupTouchEvents();
}

// Загрузка категорий
function loadCategories() {
    const categoriesGrid = document.getElementById('categoriesGrid');
    categoriesGrid.innerHTML = '';
    
    categories.forEach(category => {
        const categoryCard = createCategoryCard(category);
        categoriesGrid.appendChild(categoryCard);
    });
}

// Создание карточки категории
function createCategoryCard(category) {
    const card = document.createElement('div');
    card.className = 'category-card';
    card.dataset.categoryId = category.id;
    
    card.innerHTML = `
        <div class="category-icon">
            <i class="${category.icon}"></i>
        </div>
        <div class="category-title">${category.title}</div>
        <div class="category-description">${category.description}</div>
    `;
    
    card.addEventListener('click', () => selectCategory(category.id));
    
    return card;
}

// Выбор категории
function selectCategory(categoryId) {
    const card = document.querySelector(`[data-category-id="${categoryId}"]`);
    card.style.borderColor = 'var(--okko-accent)';
    card.style.background = 'var(--okko-accent-light)';
    
    if (!userPreferences.categories.includes(categoryId)) {
        userPreferences.categories.push(categoryId);
    }
    
    // Анимация выбора
    card.style.transform = 'scale(0.95)';
    setTimeout(() => {
        card.style.transform = 'scale(1)';
    }, 150);
}

// Загрузка рекомендаций
function loadRecommendations() {
    const carousel = document.getElementById('contentCarousel');
    carousel.innerHTML = '';
    
    // Показываем случайные рекомендации
    const shuffled = [...sampleContent].sort(() => 0.5 - Math.random());
    const recommendations = shuffled.slice(0, 5);
    
    recommendations.forEach(content => {
        const contentCard = createContentCard(content);
        carousel.appendChild(contentCard);
    });
}

// Создание карточки контента
function createContentCard(content) {
    const card = document.createElement('div');
    card.className = 'content-card';
    
    card.innerHTML = `
        <div class="content-poster" style="background-image: url('${content.poster}')"></div>
        <div class="content-info">
            <div class="content-title">${content.title}</div>
            <div class="content-meta">
                <span class="content-rating">${content.rating}</span>
                <span>${content.year}</span>
                <span>${content.genre}</span>
            </div>
        </div>
    `;
    
    card.addEventListener('click', () => showContentDetails(content));
    
    return card;
}

// Показать детали контента
function showContentDetails(content) {
    // Здесь можно добавить модальное окно с деталями
    console.log('Показать детали:', content);
}

// Загрузка интерактивного контента
function loadInteractiveContent() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';
    
    if (sampleContent.length > 0) {
        currentContent = sampleContent[0];
        const card = createInteractiveCard(currentContent);
        container.appendChild(card);
        
        // Анимация появления
        setTimeout(() => {
            card.classList.add('enter');
        }, 100);
    }
}

// Создание интерактивной карточки
function createInteractiveCard(content) {
    const card = document.createElement('div');
    card.className = 'interactive-card';
    card.dataset.contentId = content.id;
    
    card.innerHTML = `
        <div class="card-poster" style="background-image: url('${content.poster}')"></div>
        <div class="card-info">
            <div class="card-title">${content.title}</div>
            <div class="card-description">${content.description}</div>
            <div class="card-rating">
                <i class="fas fa-star"></i>
                <span>${content.rating}</span>
            </div>
        </div>
        <div class="swipe-indicator like">НРАВИТСЯ</div>
        <div class="swipe-indicator dislike">НЕ НРАВИТСЯ</div>
    `;
    
    return card;
}

// Настройка touch событий
function setupTouchEvents() {
    const container = document.getElementById('cardsContainer');
    
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    let isDragging = false;
    
    // Touch события
    container.addEventListener('touchstart', handleTouchStart, { passive: false });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd, { passive: false });
    
    // Mouse события
    container.addEventListener('mousedown', handleMouseDown);
    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('mouseup', handleMouseUp);
    
    function handleTouchStart(e) {
        if (isAnimating) return;
        
        const touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        isDragging = true;
        
        const card = getCurrentCard();
        if (card) {
            card.classList.add('swiping');
        }
    }
    
    function handleTouchMove(e) {
        if (!isDragging || isAnimating) return;
        
        e.preventDefault();
        const touch = e.touches[0];
        currentX = touch.clientX;
        currentY = touch.clientY;
        
        const deltaX = currentX - startX;
        const deltaY = currentY - startY;
        
        updateCardPosition(deltaX, deltaY);
        updateSwipeIndicators(deltaX);
    }
    
    function handleTouchEnd(e) {
        if (!isDragging || isAnimating) return;
        
        isDragging = false;
        const deltaX = currentX - startX;
        
        if (Math.abs(deltaX) > 100) {
            const action = deltaX > 0 ? 'like' : 'dislike';
            handleInteraction(action);
        } else {
            resetCardPosition();
        }
    }
    
    function handleMouseDown(e) {
        if (isAnimating) return;
        
        startX = e.clientX;
        startY = e.clientY;
        isDragging = true;
        
        const card = getCurrentCard();
        if (card) {
            card.classList.add('swiping');
        }
        
        e.preventDefault();
    }
    
    function handleMouseMove(e) {
        if (!isDragging || isAnimating) return;
        
        currentX = e.clientX;
        currentY = e.clientY;
        
        const deltaX = currentX - startX;
        const deltaY = currentY - startY;
        
        updateCardPosition(deltaX, deltaY);
        updateSwipeIndicators(deltaX);
    }
    
    function handleMouseUp(e) {
        if (!isDragging || isAnimating) return;
        
        isDragging = false;
        const deltaX = currentX - startX;
        
        if (Math.abs(deltaX) > 100) {
            const action = deltaX > 0 ? 'like' : 'dislike';
            handleInteraction(action);
        } else {
            resetCardPosition();
        }
    }
}

// Получение текущей карточки
function getCurrentCard() {
    return document.querySelector('.interactive-card');
}

// Обновление позиции карточки
function updateCardPosition(deltaX, deltaY) {
    const card = getCurrentCard();
    if (!card) return;
    
    const rotation = deltaX * 0.1;
    const opacity = Math.max(0.3, 1 - Math.abs(deltaX) / 200);
    
    card.style.transform = `translate(${deltaX}px, ${deltaY}px) rotate(${rotation}deg)`;
    card.style.opacity = opacity;
}

// Обновление индикаторов свайпа
function updateSwipeIndicators(deltaX) {
    const likeIndicator = document.querySelector('.swipe-indicator.like');
    const dislikeIndicator = document.querySelector('.swipe-indicator.dislike');
    
    if (deltaX > 50) {
        likeIndicator.classList.add('show');
        dislikeIndicator.classList.remove('show');
    } else if (deltaX < -50) {
        dislikeIndicator.classList.add('show');
        likeIndicator.classList.remove('show');
    } else {
        likeIndicator.classList.remove('show');
        dislikeIndicator.classList.remove('show');
    }
}

// Сброс позиции карточки
function resetCardPosition() {
    const card = getCurrentCard();
    if (!card) return;
    
    card.style.transform = '';
    card.style.opacity = '';
    card.classList.remove('swiping');
    
    document.querySelectorAll('.swipe-indicator').forEach(indicator => {
        indicator.classList.remove('show');
    });
}

// Обработка взаимодействия
async function handleInteraction(action) {
    if (isAnimating || !currentContent) return;
    
    isAnimating = true;
    const card = getCurrentCard();
    
    if (card) {
        // Анимация свайпа
        card.classList.add(action);
        
        // Обновление статистики
        if (action === 'like') {
            likedCount++;
            userPreferences.genres.push(currentContent.genre);
            userPreferences.ratings.push(currentContent.rating);
        } else {
            dislikedCount++;
        }
        
        updateStats();
        
        // Haptic feedback
        if ('vibrate' in navigator) {
            navigator.vibrate(50);
        }
        
        // Загрузка следующего контента
        setTimeout(() => {
            loadNextContent();
            isAnimating = false;
        }, 300);
    }
}

// Загрузка следующего контента
function loadNextContent() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';
    
    // Находим следующий контент
    const currentIndex = sampleContent.findIndex(item => item.id === currentContent.id);
    const nextIndex = (currentIndex + 1) % sampleContent.length;
    
    if (nextIndex === 0) {
        // Показать экран завершения
        showCompletionScreen();
        return;
    }
    
    currentContent = sampleContent[nextIndex];
    const card = createInteractiveCard(currentContent);
    container.appendChild(card);
    
    setTimeout(() => {
        card.classList.add('enter');
    }, 100);
}

// Обновление статистики
function updateStats() {
    document.getElementById('likedCount').textContent = likedCount;
    document.getElementById('dislikedCount').textContent = dislikedCount;
    
    // Расчет точности (простая формула)
    const total = likedCount + dislikedCount;
    const accuracy = total > 0 ? Math.round((likedCount / total) * 100) : 0;
    document.getElementById('accuracyScore').textContent = accuracy + '%';
}

// Показать экран завершения
function showCompletionScreen() {
    document.getElementById('completionScreen').style.display = 'flex';
}

// Показать рекомендации
function showRecommendations() {
    document.getElementById('completionScreen').style.display = 'none';
    loadRecommendations();
}

// Перезапуск анализа
function restartAnalysis() {
    document.getElementById('completionScreen').style.display = 'none';
    
    // Сброс данных
    likedCount = 0;
    dislikedCount = 0;
    userPreferences = { categories: [], genres: [], ratings: [] };
    
    updateStats();
    loadInteractiveContent();
}

// Анимация появления элементов
function animateOnScroll() {
    const elements = document.querySelectorAll('.category-card, .content-card, .stat-card');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    elements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'all 0.6s ease';
        observer.observe(element);
    });
}

// Инициализация анимаций
setTimeout(animateOnScroll, 500);