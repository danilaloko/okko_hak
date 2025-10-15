/* ==============================
   Results - Экран результатов и рекомендаций
   ============================== */

// Глобальные переменные
let currentRecommendations = [];
let currentFilters = {
    platform: '',
    language: '',
    duration: '',
    novelty: ''
};
let diversificationLevel = 0.5;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeResults();
});

// Основная инициализация
function initializeResults() {
    hideLoadingScreen();
    setupEventListeners();
    loadRecommendations();
    setupFilters();
}

// Скрытие загрузочного экрана
function hideLoadingScreen() {
    setTimeout(() => {
        const loadingScreen = document.getElementById('loadingScreen');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
        }
    }, 1000);
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Кнопка назад
    const backBtn = document.getElementById('backBtn');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            window.location.href = '/';
        });
    }
    
    // Кнопка поделиться
    const shareBtn = document.getElementById('shareBtn');
    if (shareBtn) {
        shareBtn.addEventListener('click', () => {
            shareResults();
        });
    }
    
    // Переключатель фильтров
    const filterToggle = document.getElementById('filterToggle');
    if (filterToggle) {
        filterToggle.addEventListener('click', () => {
            toggleFilters();
        });
    }
    
    // Фильтры
    const platformFilter = document.getElementById('platformFilter');
    const languageFilter = document.getElementById('languageFilter');
    const durationFilter = document.getElementById('durationFilter');
    const noveltyFilter = document.getElementById('noveltyFilter');
    
    if (platformFilter) {
        platformFilter.addEventListener('change', (e) => {
            currentFilters.platform = e.target.value;
            applyFilters();
        });
    }
    if (languageFilter) {
        languageFilter.addEventListener('change', (e) => {
            currentFilters.language = e.target.value;
            applyFilters();
        });
    }
    if (durationFilter) {
        durationFilter.addEventListener('change', (e) => {
            currentFilters.duration = e.target.value;
            applyFilters();
        });
    }
    if (noveltyFilter) {
        noveltyFilter.addEventListener('change', (e) => {
            currentFilters.novelty = e.target.value;
            applyFilters();
        });
    }
    
    // Слайдер диверсификации
    const diversificationSlider = document.getElementById('diversificationSlider');
    if (diversificationSlider) {
        diversificationSlider.addEventListener('input', (e) => {
            diversificationLevel = parseFloat(e.target.value);
            applyDiversification();
        });
    }
    
    // Кнопки действий
    const saveSetBtn = document.getElementById('saveSetBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    
    if (saveSetBtn) {
        saveSetBtn.addEventListener('click', () => {
            showSaveSetModal();
        });
    }
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadRecommendations();
        });
    }
    
    // Модальные окна
    const modalClose = document.getElementById('modalClose');
    const saveSetModalClose = document.getElementById('saveSetModalClose');
    const confirmSaveSetBtn = document.getElementById('confirmSaveSetBtn');
    
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            hideModal();
        });
    }
    if (saveSetModalClose) {
        saveSetModalClose.addEventListener('click', () => {
            hideSaveSetModal();
        });
    }
    if (confirmSaveSetBtn) {
        confirmSaveSetBtn.addEventListener('click', () => {
            saveSet();
        });
    }
}

// Загрузка рекомендаций
async function loadRecommendations() {
    try {
        showLoadingScreen('Формируем рекомендации...', 'Анализируем ваши предпочтения');
        
        const response = await fetch('/api/results');
        if (response.ok) {
            const data = await response.json();
            currentRecommendations = data.recommendations;
            displayRecommendations(data.recommendations);
            updateRecommendationsCount(data.recommendations.length);
        } else {
            throw new Error('Ошибка загрузки рекомендаций');
        }
    } catch (error) {
        console.error('Ошибка загрузки рекомендаций:', error);
        showErrorMessage('Ошибка загрузки рекомендаций. Попробуйте еще раз.');
    } finally {
        hideLoadingScreen();
    }
}

// Отображение рекомендаций
function displayRecommendations(recommendations) {
    const recommendationsList = document.getElementById('recommendationsList');
    if (!recommendationsList) return;
    
    recommendationsList.innerHTML = recommendations
        .map(rec => `
            <div class="recommendation-card" data-movie-id="${rec.id}">
                <div class="recommendation-poster" style="background-image: url('${rec.poster}')"></div>
                <div class="recommendation-info">
                    <div class="recommendation-title">${rec.title}</div>
                    <div class="recommendation-meta">
                        <span class="recommendation-year">${rec.year}</span>
                        <span class="recommendation-genre">${rec.genre}</span>
                        <span class="recommendation-rating">${rec.rating}</span>
                    </div>
                    <div class="recommendation-reason">${rec.reason}</div>
                    <div class="recommendation-actions">
                        <button class="action-btn primary-btn" onclick="showMovieDetails(${rec.id})">
                            <i class="fas fa-info-circle"></i>
                            Подробнее
                        </button>
                        <button class="action-btn secondary-btn" onclick="addToWatchlist(${rec.id})">
                            <i class="fas fa-plus"></i>
                            В список
                        </button>
                    </div>
                </div>
            </div>
        `)
        .join('');
}

// Обновление счетчика рекомендаций
function updateRecommendationsCount(count) {
    const countEl = document.getElementById('recommendationsCount');
    if (countEl) {
        countEl.textContent = count;
    }
}

// Настройка фильтров
function setupFilters() {
    // Инициализация фильтров
    const filtersContent = document.getElementById('filtersContent');
    if (filtersContent) {
        filtersContent.style.display = 'none';
    }
}

// Переключение фильтров
function toggleFilters() {
    const filtersContent = document.getElementById('filtersContent');
    const filterToggle = document.getElementById('filterToggle');
    
    if (filtersContent && filterToggle) {
        const isVisible = filtersContent.style.display !== 'none';
        filtersContent.style.display = isVisible ? 'none' : 'block';
        filterToggle.classList.toggle('active', !isVisible);
    }
}

// Применение фильтров
function applyFilters() {
    let filteredRecommendations = [...currentRecommendations];
    
    // Фильтр по платформе
    if (currentFilters.platform) {
        // Здесь должна быть логика фильтрации по платформе
        console.log('Фильтр по платформе:', currentFilters.platform);
    }
    
    // Фильтр по языку
    if (currentFilters.language) {
        // Здесь должна быть логика фильтрации по языку
        console.log('Фильтр по языку:', currentFilters.language);
    }
    
    // Фильтр по длительности
    if (currentFilters.duration) {
        // Здесь должна быть логика фильтрации по длительности
        console.log('Фильтр по длительности:', currentFilters.duration);
    }
    
    // Фильтр по новизне
    if (currentFilters.novelty) {
        // Здесь должна быть логика фильтрации по новизне
        console.log('Фильтр по новизне:', currentFilters.novelty);
    }
    
    displayRecommendations(filteredRecommendations);
    updateRecommendationsCount(filteredRecommendations.length);
}

// Применение диверсификации
function applyDiversification() {
    // Здесь должна быть логика изменения алгоритма рекомендаций
    // на основе уровня диверсификации
    console.log('Уровень диверсификации:', diversificationLevel);
    
    // Перезагружаем рекомендации с новым уровнем диверсификации
    loadRecommendations();
}

// Показать детали фильма
function showMovieDetails(movieId) {
    const movie = currentRecommendations.find(rec => rec.id === movieId);
    if (!movie) return;
    
    const modal = document.getElementById('movieModal');
    const movieTitle = document.getElementById('movieTitle');
    const movieDetails = document.getElementById('movieDetails');
    
    if (modal && movieTitle && movieDetails) {
        movieTitle.textContent = movie.title;
        movieDetails.innerHTML = `
            <div class="movie-details-content">
                <div class="movie-poster" style="background-image: url('${movie.poster}')"></div>
                <div class="movie-info">
                    <div class="movie-year">${movie.year}</div>
                    <div class="movie-genre">${movie.genre}</div>
                    <div class="movie-rating">Рейтинг: ${movie.rating}</div>
                    <div class="movie-description">${movie.description}</div>
                    <div class="movie-reason">${movie.reason}</div>
                </div>
            </div>
        `;
        modal.classList.add('active');
    }
}

// Добавить в список просмотра
function addToWatchlist(movieId) {
    const movie = currentRecommendations.find(rec => rec.id === movieId);
    if (movie) {
        // Здесь должна быть логика добавления в список просмотра
        console.log('Добавляем в список просмотра:', movie.title);
        
        // Визуальная обратная связь
        const button = event.target.closest('.action-btn');
        if (button) {
            button.innerHTML = '<i class="fas fa-check"></i> Добавлено';
            button.classList.add('success');
        }
    }
}

// Показать модальное окно сохранения сета
function showSaveSetModal() {
    const modal = document.getElementById('saveSetModal');
    const selectedMovies = document.getElementById('selectedMovies');
    
    if (modal && selectedMovies) {
        // Показываем выбранные фильмы
        selectedMovies.innerHTML = currentRecommendations
            .slice(0, 3) // Показываем первые 3 рекомендации
            .map(rec => `
                <div class="selected-movie">
                    <div class="movie-poster" style="background-image: url('${rec.poster}')"></div>
                    <div class="movie-title">${rec.title}</div>
                </div>
            `)
            .join('');
        
        modal.classList.add('active');
    }
}

// Скрыть модальное окно сохранения сета
function hideSaveSetModal() {
    const modal = document.getElementById('saveSetModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Сохранение сета
function saveSet() {
    const setName = document.getElementById('setName').value;
    const setDescription = document.getElementById('setDescription').value;
    
    if (!setName.trim()) {
        alert('Пожалуйста, введите название сета');
        return;
    }
    
    // Здесь должна быть логика сохранения сета
    console.log('Сохраняем сет:', { name: setName, description: setDescription });
    
    // Показываем сообщение об успехе
    alert('Сет успешно сохранен!');
    hideSaveSetModal();
}

// Поделиться результатами
function shareResults() {
    if (navigator.share) {
        navigator.share({
            title: 'Мои рекомендации фильмов',
            text: 'Посмотрите на мои персонализированные рекомендации фильмов!',
            url: window.location.href
        });
    } else {
        // Fallback для браузеров без поддержки Web Share API
        const shareText = `Мои рекомендации фильмов: ${window.location.href}`;
        navigator.clipboard.writeText(shareText).then(() => {
            alert('Ссылка скопирована в буфер обмена!');
        });
    }
}

// Показать сообщение об ошибке
function showErrorMessage(message) {
    const recommendationsList = document.getElementById('recommendationsList');
    if (recommendationsList) {
        recommendationsList.innerHTML = `
            <div class="error-message">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3>Ошибка загрузки</h3>
                <p>${message}</p>
                <button class="action-btn primary-btn" onclick="loadRecommendations()">
                    <i class="fas fa-redo"></i>
                    Попробовать еще раз
                </button>
            </div>
        `;
    }
}

// Показать загрузочный экран
function showLoadingScreen(title, text) {
    const loadingScreen = document.getElementById('loadingScreen');
    const loadingTitle = document.querySelector('.loading-title');
    const loadingText = document.querySelector('.loading-text');
    
    if (loadingScreen) {
        loadingScreen.style.display = 'flex';
    }
    if (loadingTitle && title) {
        loadingTitle.textContent = title;
    }
    if (loadingText && text) {
        loadingText.textContent = text;
    }
}

// Скрыть загрузочный экран
function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.style.display = 'none';
    }
}

// Скрыть модальное окно
function hideModal() {
    const modal = document.getElementById('movieModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Анимация появления элементов
function animateOnScroll() {
    const elements = document.querySelectorAll('.recommendation-card, .filter-group');
    
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
