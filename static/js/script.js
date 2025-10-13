// Глобальные переменные
let currentMovie = null;
let likedCount = 0;
let dislikedCount = 0;
let isAnimating = false;

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    hideLoadingScreen();
    loadCurrentMovie();
    setupTouchEvents();
});

// Скрытие загрузочного экрана
function hideLoadingScreen() {
    setTimeout(() => {
        const loadingScreen = document.getElementById('loadingScreen');
        loadingScreen.classList.add('hidden');
    }, 1000);
}

// Загрузка текущего фильма
async function loadCurrentMovie() {
    try {
        const response = await fetch('/api/current-movie');
        if (response.ok) {
            currentMovie = await response.json();
            displayMovie(currentMovie);
        } else {
            showNoMoreMovies();
        }
    } catch (error) {
        console.error('Ошибка загрузки фильма:', error);
        showNoMoreMovies();
    }
}

// Отображение фильма
function displayMovie(movie) {
    const cardsContainer = document.getElementById('cardsContainer');
    cardsContainer.innerHTML = '';

    const card = createMovieCard(movie);
    cardsContainer.appendChild(card);

    // Анимация появления
    setTimeout(() => {
        card.classList.add('enter');
    }, 100);
}

// Создание карточки фильма
function createMovieCard(movie) {
    const card = document.createElement('div');
    card.className = 'movie-card';
    card.dataset.movieId = movie.id;

    card.innerHTML = `
        <div class="movie-poster" style="background-image: url('${movie.poster}')"></div>
        <div class="movie-info">
            <h2 class="movie-title">${movie.title}</h2>
            <div class="movie-year">${movie.year}</div>
            <div class="movie-genre">${movie.genre}</div>
            <div class="movie-description">${movie.description}</div>
            <div class="movie-rating">
                <i class="fas fa-star"></i>
                <span>${movie.rating}/10</span>
            </div>
        </div>
        <div class="swipe-indicator like">❤️ НРАВИТСЯ</div>
        <div class="swipe-indicator dislike">💔 НЕ НРАВИТСЯ</div>
    `;

    return card;
}

// Настройка touch событий
function setupTouchEvents() {
    const cardsContainer = document.getElementById('cardsContainer');
    
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    let isDragging = false;

    // Touch события
    cardsContainer.addEventListener('touchstart', handleTouchStart, { passive: false });
    cardsContainer.addEventListener('touchmove', handleTouchMove, { passive: false });
    cardsContainer.addEventListener('touchend', handleTouchEnd, { passive: false });

    // Mouse события для десктопа
    cardsContainer.addEventListener('mousedown', handleMouseDown);
    cardsContainer.addEventListener('mousemove', handleMouseMove);
    cardsContainer.addEventListener('mouseup', handleMouseUp);

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
            swipeMovie(action);
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
            swipeMovie(action);
        } else {
            resetCardPosition();
        }
    }
}

// Получение текущей карточки
function getCurrentCard() {
    return document.querySelector('.movie-card');
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
    
    // Скрыть индикаторы
    document.querySelectorAll('.swipe-indicator').forEach(indicator => {
        indicator.classList.remove('show');
    });
}

// Свайп фильма
async function swipeMovie(action) {
    if (isAnimating || !currentMovie) return;
    
    isAnimating = true;
    const card = getCurrentCard();
    
    if (card) {
        // Анимация свайпа
        card.classList.add(action);
        
        // Обновление статистики
        if (action === 'like') {
            likedCount++;
            document.getElementById('likedCount').textContent = likedCount;
        } else {
            dislikedCount++;
            document.getElementById('dislikedCount').textContent = dislikedCount;
        }
        
        // Отправка на сервер
        try {
            const response = await fetch('/api/swipe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: action })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.next_available) {
                    // Загрузка следующего фильма
                    setTimeout(() => {
                        loadCurrentMovie();
                        isAnimating = false;
                    }, 300);
                } else {
                    // Показать сообщение о завершении
                    setTimeout(() => {
                        showNoMoreMovies();
                        isAnimating = false;
                    }, 300);
                }
            }
        } catch (error) {
            console.error('Ошибка отправки свайпа:', error);
            isAnimating = false;
        }
    }
}

// Показать сообщение о завершении
function showNoMoreMovies() {
    document.getElementById('cardsContainer').style.display = 'none';
    document.getElementById('actionButtons').style.display = 'none';
    document.getElementById('noMoreMovies').style.display = 'block';
}

// Сброс фильмов
async function resetMovies() {
    try {
        const response = await fetch('/api/reset');
        if (response.ok) {
            // Сброс статистики
            likedCount = 0;
            dislikedCount = 0;
            document.getElementById('likedCount').textContent = '0';
            document.getElementById('dislikedCount').textContent = '0';
            
            // Показать контейнер карточек
            document.getElementById('cardsContainer').style.display = 'block';
            document.getElementById('actionButtons').style.display = 'flex';
            document.getElementById('noMoreMovies').style.display = 'none';
            
            // Загрузить первый фильм
            loadCurrentMovie();
        }
    } catch (error) {
        console.error('Ошибка сброса:', error);
    }
}

// Добавление haptic feedback для мобильных устройств
function addHapticFeedback(type = 'light') {
    if ('vibrate' in navigator) {
        const patterns = {
            light: [50],
            medium: [100],
            heavy: [200],
            success: [50, 50, 100]
        };
        navigator.vibrate(patterns[type] || patterns.light);
    }
}

// Добавление визуальных эффектов
function addVisualEffect(type, element) {
    const effects = {
        sparkle: () => createSparkleEffect(element),
        pulse: () => element.style.animation = 'pulse 0.3s ease-out',
        shake: () => element.style.animation = 'shake 0.5s ease-out'
    };
    
    if (effects[type]) {
        effects[type]();
    }
}

// Создание эффекта искр
function createSparkleEffect(element) {
    const sparkles = 5;
    for (let i = 0; i < sparkles; i++) {
        const sparkle = document.createElement('div');
        sparkle.className = 'sparkle';
        sparkle.style.cssText = `
            position: absolute;
            width: 4px;
            height: 4px;
            background: radial-gradient(circle, #ffd700, transparent);
            border-radius: 50%;
            pointer-events: none;
            z-index: 1000;
            animation: sparkleAnimation 1s ease-out forwards;
        `;
        
        const rect = element.getBoundingClientRect();
        sparkle.style.left = (rect.left + Math.random() * rect.width) + 'px';
        sparkle.style.top = (rect.top + Math.random() * rect.height) + 'px';
        
        document.body.appendChild(sparkle);
        
        setTimeout(() => sparkle.remove(), 1000);
    }
}

// Улучшенная обработка свайпов с эффектами
const originalSwipeMovie = swipeMovie;
swipeMovie = function(action) {
    addHapticFeedback(action === 'like' ? 'success' : 'medium');
    
    const card = getCurrentCard();
    if (card) {
        addVisualEffect('sparkle', card);
    }
    
    return originalSwipeMovie(action);
};

// Предотвращение случайных свайпов
let swipeStartTime = 0;
document.addEventListener('touchstart', function() {
    swipeStartTime = Date.now();
});

// Добавление минимального времени для свайпа
const originalHandleTouchEnd = handleTouchEnd;
function handleTouchEnd(e) {
    const swipeDuration = Date.now() - swipeStartTime;
    if (swipeDuration < 100) return; // Минимум 100мс для свайпа
    
    return originalHandleTouchEnd(e);
}
