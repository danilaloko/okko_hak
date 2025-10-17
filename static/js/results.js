/* ==============================
   Results - Экран результатов и рекомендаций
   ============================== */

// Глобальные переменные
let currentRecommendations = [];
let selectionHistory = [];
let currentFilters = {
    platform: '',
    language: '',
    duration: '',
    novelty: ''
};
let diversificationLevel = 0.5;
let okkonatorRecommendations = [];
let okkonatorProfile = {};
let swipeRecommendations = [];
let swipeProfile = {};
let currentDataSource = 'okkonator'; // 'okkonator' или 'swipe'

// Функции логгирования
function log(message, data = null) {
    console.log(`[Результаты] ${message}`, data || '');
}

function logError(message, error = null) {
    console.error(`[Результаты ОШИБКА] ${message}`, error || '');
}

function logSuccess(message, data = null) {
    console.log(`[Результаты УСПЕХ] ${message}`, data || '');
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    log('Инициализация страницы результатов');
    initializeResults();
});

// Основная инициализация
function initializeResults() {
    log('Начинаем инициализацию результатов');
    hideLoadingScreen();
    setupEventListeners();
    loadSelectionHistory();
    loadOkkonatorRecommendations();
    loadSwipeRecommendations();
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

// Загрузка истории подборок
async function loadSelectionHistory() {
    try {
        const response = await fetch('/api/history');
        if (response.ok) {
            const data = await response.json();
            selectionHistory = data.history;
            displaySelectionHistory(data.history);
            updateHistoryStats(data.total);
        } else {
            throw new Error('Ошибка загрузки истории');
        }
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
    }
}

// Загрузка рекомендаций от Окконатора
function loadOkkonatorRecommendations() {
    log('Проверяем наличие рекомендаций от Окконатора в localStorage');
    
    const storedRecommendations = localStorage.getItem('okkonator_recommendations');
    const storedProfile = localStorage.getItem('okkonator_profile');
    
    if (storedRecommendations) {
        try {
            okkonatorRecommendations = JSON.parse(storedRecommendations);
            logSuccess(`Загружено ${okkonatorRecommendations.length} рекомендаций от Окконатора`);
            
            if (storedProfile) {
                okkonatorProfile = JSON.parse(storedProfile);
                log('Загружен профиль Окконатора:', okkonatorProfile);
            }
            
            // Показываем рекомендации от Окконатора
            displayOkkonatorRecommendations();
            
            // Очищаем localStorage после использования
            localStorage.removeItem('okkonator_recommendations');
            localStorage.removeItem('okkonator_profile');
            
        } catch (error) {
            logError('Ошибка парсинга рекомендаций от Окконатора:', error);
        }
    } else {
        log('Рекомендации от Окконатора не найдены, загружаем обычные рекомендации');
    }
}

function loadSwipeRecommendations() {
    log('Проверяем наличие рекомендаций от свайпов в localStorage');
    
    const storedRecommendations = localStorage.getItem('swipeRecommendations');
    const storedProfile = localStorage.getItem('userProfile');
    
    if (storedRecommendations) {
        try {
            swipeRecommendations = JSON.parse(storedRecommendations);
            logSuccess(`Загружено ${swipeRecommendations.length} рекомендаций от свайпов`);
            
            if (storedProfile) {
                swipeProfile = JSON.parse(storedProfile);
                log('Загружен профиль свайпов:', swipeProfile);
            }
            
            // Показываем рекомендации от свайпов
            displaySwipeRecommendations();
            
            // Очищаем localStorage после использования
            localStorage.removeItem('swipeRecommendations');
            localStorage.removeItem('userProfile');
            
        } catch (error) {
            logError('Ошибка парсинга рекомендаций от свайпов:', error);
        }
    } else {
        log('Рекомендации от свайпов не найдены');
    }
}

// Отображение рекомендаций от Окконатора
function displayOkkonatorRecommendations() {
    log('Отображаем рекомендации от Окконатора');
    
    const recommendationsContainer = document.getElementById('recommendationsContainer');
    if (!recommendationsContainer) {
        logError('Контейнер рекомендаций не найден');
        return;
    }
    
    // Очищаем контейнер
    recommendationsContainer.innerHTML = '';
    
    // Добавляем заголовок
    const header = document.createElement('div');
    header.className = 'recommendations-header';
    header.innerHTML = `
        <h2>🎯 Рекомендации от Окконатора</h2>
        <p>На основе ваших ответов мы подобрали идеальные фильмы для вас</p>
    `;
    recommendationsContainer.appendChild(header);
    
    // Добавляем рекомендации
    const grid = document.createElement('div');
    grid.className = 'recommendations-grid';
    
    okkonatorRecommendations.forEach((movie, index) => {
        const card = createMovieCard(movie, index, 'okkonator');
        grid.appendChild(card);
    });
    
    recommendationsContainer.appendChild(grid);
}

// Отображение рекомендаций от свайпов
function displaySwipeRecommendations() {
    log('Отображаем рекомендации от свайпов');
    
    const recommendationsContainer = document.getElementById('recommendationsContainer');
    if (!recommendationsContainer) {
        logError('Контейнер рекомендаций не найден');
        return;
    }
    
    // Очищаем контейнер
    recommendationsContainer.innerHTML = '';
    
    // Добавляем заголовок
    const header = document.createElement('div');
    header.className = 'recommendations-header';
    header.innerHTML = `
        <h2>💫 Рекомендации на основе свайпов</h2>
        <p>Мы изучили ваши предпочтения и подобрали идеальные фильмы</p>
    `;
    recommendationsContainer.appendChild(header);
    
    // Добавляем рекомендации
    const grid = document.createElement('div');
    grid.className = 'recommendations-grid';
    
    swipeRecommendations.forEach((movie, index) => {
        const card = createMovieCard(movie, index, 'swipe');
        grid.appendChild(card);
    });
    
    recommendationsContainer.appendChild(grid);
    
    logSuccess(`Отображено ${swipeRecommendations.length} рекомендаций от свайпов`);
}

// Создание карточки фильма
function createMovieCard(movie, index, source = 'default') {
    // Функция для очистки данных от квадратных скобок
    function cleanData(data) {
        if (!data) return '';
        return data.toString().replace(/[\[\]']/g, '').replace(/'/g, '');
    }
    
    const card = document.createElement('div');
    card.className = `movie-card ${source}`;
    card.style.cursor = movie.url ? 'pointer' : 'default';
    
    card.innerHTML = `
        <div style="padding: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 16px; color: var(--okko-text); font-weight: 600; flex: 1;">${movie.title}</h3>
                <div style="display: flex; gap: 6px; margin-left: 10px;">
                    <span style="background: rgba(239, 68, 68, 0.9); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">${movie.age_rating || 'N/A'}</span>
                    <span style="background: rgba(123, 97, 255, 0.9); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">${movie.content_type || 'Контент'}</span>
                </div>
            </div>
            <p style="margin: 0 0 4px 0; font-size: 13px; color: var(--okko-text-muted);">${cleanData(movie.country) || 'Страна не указана'}</p>
            <p style="margin: 0 0 6px 0; font-size: 12px; color: var(--okko-text-muted-2);">${cleanData(movie.genres) || 'Жанры не указаны'}</p>
            ${movie.reason ? `<p style="margin: 0 0 6px 0; font-size: 11px; color: var(--okko-accent); font-style: italic;">${movie.reason}</p>` : ''}
            ${movie.description ? `<p style="margin: 0 0 8px 0; font-size: 11px; color: var(--okko-text-muted-2); line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${movie.description}</p>` : ''}
            <div style="display: flex; gap: 8px; margin-top: 8px;">
                <button class="action-btn like-btn" onclick="event.stopPropagation(); likeMovie(${index}, '${source}')" style="background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.5); color: #EF4444; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all 0.3s ease;">
                    <i class="fas fa-heart"></i> Лайк
                </button>
                <button class="action-btn watch-btn" onclick="event.stopPropagation(); watchMovie(${index}, '${source}')" style="background: rgba(123, 97, 255, 0.2); border: 1px solid rgba(123, 97, 255, 0.5); color: #7B61FF; padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; transition: all 0.3s ease;">
                    <i class="fas fa-play"></i> Смотреть
                </button>
            </div>
        </div>
    `;
    
    // Добавляем клик для открытия ссылки
    if (movie.url) {
        card.addEventListener('click', () => {
            window.open(movie.url, '_blank');
        });
    }
    
    return card;
}

// Обработка лайка фильма
function likeMovie(index, source) {
    log(`Лайк фильма ${index} из источника ${source}`);
    
    const movie = source === 'okkonator' ? okkonatorRecommendations[index] : currentRecommendations[index];
    if (movie) {
        logSuccess(`Добавлен в избранное: ${movie.title}`);
        // Здесь можно добавить логику сохранения в избранное
        showSuccessMessage(`"${movie.title}" добавлен в избранное!`);
    }
}

// Обработка просмотра фильма
function watchMovie(index, source) {
    log(`Просмотр фильма ${index} из источника ${source}`);
    
    const movie = source === 'okkonator' ? okkonatorRecommendations[index] : currentRecommendations[index];
    if (movie) {
        logSuccess(`Начинаем просмотр: ${movie.title}`);
        showSuccessMessage(`Переходим к просмотру "${movie.title}"!`);
        // Здесь можно добавить логику перехода к просмотру
    }
}

// Показать сообщение об успехе
function showSuccessMessage(message) {
    // Создаем временное уведомление
    const notification = document.createElement('div');
    notification.className = 'success-notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--okko-success);
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        z-index: 1000;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    document.body.appendChild(notification);
    
    // Удаляем через 3 секунды
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
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
    
    // Функция для очистки данных от квадратных скобок
    function cleanData(data) {
        if (!data) return '';
        return data.toString().replace(/[\[\]']/g, '').replace(/'/g, '');
    }
    
    recommendationsList.innerHTML = recommendations
        .map(rec => `
            <div class="recommendation-card" data-movie-id="${rec.id}" style="cursor: ${rec.url ? 'pointer' : 'default'};">
                <div class="recommendation-poster" style="background-image: url('${rec.poster}')">
                    <div class="poster-overlay">
                        <div class="age-rating">${rec.age_rating || 'N/A'}</div>
                        <div class="content-type">${rec.content_type || 'Контент'}</div>
                    </div>
                </div>
                <div class="recommendation-info">
                    <div class="recommendation-title">${rec.title}</div>
                    <div class="recommendation-meta">
                        <span class="recommendation-country">${cleanData(rec.country) || 'Страна не указана'}</span>
                        <span class="recommendation-genres">${cleanData(rec.genres) || 'Жанры не указаны'}</span>
                    </div>
                    <div class="recommendation-reason">${rec.reason}</div>
                    ${rec.description ? `<div class="recommendation-description">${rec.description}</div>` : ''}
                    <div class="recommendation-actions">
                        <button class="action-btn primary-btn" onclick="event.stopPropagation(); showMovieDetails(${rec.id})">
                            <i class="fas fa-info-circle"></i>
                            Подробнее
                        </button>
                        <button class="action-btn secondary-btn" onclick="event.stopPropagation(); addToWatchlist(${rec.id})">
                            <i class="fas fa-plus"></i>
                            В список
                        </button>
                    </div>
                </div>
            </div>
        `)
        .join('');
    
    // Добавляем обработчики кликов для карточек
    recommendations.forEach((rec, index) => {
        if (rec.url) {
            const card = recommendationsList.children[index];
            if (card) {
                card.addEventListener('click', () => {
                    window.open(rec.url, '_blank');
                });
            }
        }
    });
}

// Отображение истории подборок
function displaySelectionHistory(history) {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;
    
    historyList.innerHTML = history
        .map(selection => `
            <div class="history-item">
                <div class="history-header">
                    <div class="history-date">${formatDate(selection.date)}</div>
                    <div class="history-method">${selection.method}</div>
                </div>
                <div class="history-movies">
                    <div class="movies-scroll-container">
                        ${selection.movies.map(movie => `
                            <div class="history-movie-card" data-movie-id="${movie.id}">
                                <div class="movie-poster" style="background-image: url('${movie.poster}')"></div>
                                <div class="movie-title">${movie.title}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `)
        .join('');
}

// Обновление статистики истории
function updateHistoryStats(total) {
    const totalEl = document.getElementById('totalSelections');
    if (totalEl) {
        totalEl.textContent = total;
    }
}

// Форматирование даты
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('ru-RU', options);
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
