/* ==============================
   Swipe - Экран свайпов
   ============================== */

// Глобальные переменные
let currentSwipeType = 'movies';
let currentCards = [];
let currentCardIndex = 0;
let swipeCount = 0;
let totalSwipes = 20;
let isAnimating = false;
let currentCard = null;
let isInitialized = false;
let sessionId = null;
let swipeServiceUrl = 'http://localhost:5002'; // URL микросервиса свайпов
let userVector = null; // Вектор пользователя
let swipeHistory = []; // История свайпов
let likedMovies = []; // Лайкнутые фильмы
let dislikedMovies = []; // Дизлайкнутые фильмы

// Ключи для localStorage
const STORAGE_KEYS = {
    USER_VECTOR: 'swipe_user_vector',
    SWIPE_HISTORY: 'swipe_history',
    LIKED_MOVIES: 'swipe_liked_movies',
    DISLIKED_MOVIES: 'swipe_disliked_movies',
    SWIPE_COUNT: 'swipe_count',
    CURRENT_CARD_INDEX: 'swipe_current_card_index',
    CURRENT_CARDS: 'swipe_current_cards',
    SESSION_ID: 'swipe_session_id',
    RECOMMENDATIONS: 'swipe_recommendations',
    SHOW_RESULTS: 'swipe_show_results'
};

// Функции для работы с localStorage
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        console.log(`[Свайпы] Сохранено в localStorage: ${key}`, data);
    } catch (error) {
        console.error(`[Свайпы] Ошибка сохранения в localStorage: ${key}`, error);
    }
}

function loadFromStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(key);
        if (data) {
            const parsed = JSON.parse(data);
            console.log(`[Свайпы] Загружено из localStorage: ${key}`, parsed);
            return parsed;
        }
    } catch (error) {
        console.error(`[Свайпы] Ошибка загрузки из localStorage: ${key}`, error);
    }
    return defaultValue;
}

function clearStorage() {
    try {
        Object.values(STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
        console.log('[Свайпы] Очищен localStorage');
    } catch (error) {
        console.error('[Свайпы] Ошибка очистки localStorage', error);
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeSwipe();
});

// Основная инициализация
function initializeSwipe() {
    if (isInitialized) return;
    
    hideLoadingScreen();
    setupEventListeners();
    loadUserData();
    
    // Проверяем, нужно ли показать результаты
    const showResults = loadFromStorage(STORAGE_KEYS.SHOW_RESULTS, false);
    if (showResults) {
        console.log('[Свайпы] Показываем сохраненные результаты');
        showSavedResults();
        return;
    }
    
    // Проверяем, завершены ли свайпы (дополнительная проверка)
    if (swipeCount >= totalSwipes || currentCardIndex >= currentCards.length) {
        console.log('[Свайпы] Свайпы уже завершены при загрузке, показываем результаты');
        showResultsOnSamePage();
        return;
    }
    
    loadCards();
    updateProgress();
    isInitialized = true;
}

// Загрузка данных пользователя из localStorage
function loadUserData() {
    console.log('[Свайпы] Загружаем данные пользователя из localStorage');
    
    // Загружаем вектор пользователя
    userVector = loadFromStorage(STORAGE_KEYS.USER_VECTOR, null);
    
    // Загружаем историю свайпов
    swipeHistory = loadFromStorage(STORAGE_KEYS.SWIPE_HISTORY, []);
    
    // Загружаем лайкнутые и дизлайкнутые фильмы
    likedMovies = loadFromStorage(STORAGE_KEYS.LIKED_MOVIES, []);
    dislikedMovies = loadFromStorage(STORAGE_KEYS.DISLIKED_MOVIES, []);
    
    // Загружаем счетчики
    swipeCount = loadFromStorage(STORAGE_KEYS.SWIPE_COUNT, 0);
    currentCardIndex = loadFromStorage(STORAGE_KEYS.CURRENT_CARD_INDEX, 0);
    
    // Загружаем текущие карточки
    currentCards = loadFromStorage(STORAGE_KEYS.CURRENT_CARDS, []);
    
    // Загружаем session ID
    sessionId = loadFromStorage(STORAGE_KEYS.SESSION_ID, null);
    
    console.log(`[Свайпы] Загружены данные: свайпов=${swipeCount}, карточка=${currentCardIndex}, вектор=${userVector ? 'есть' : 'нет'}`);
    
    // Дополнительная проверка: если свайпы завершены, но флаг SHOW_RESULTS не установлен
    if (swipeCount >= totalSwipes && !loadFromStorage(STORAGE_KEYS.SHOW_RESULTS, false)) {
        console.log('[Свайпы] Свайпы завершены, но флаг SHOW_RESULTS не установлен. Устанавливаем флаг и показываем результаты.');
        saveToStorage(STORAGE_KEYS.SHOW_RESULTS, true);
    }
}

// Показать сохраненные результаты
async function showSavedResults() {
    console.log('[Свайпы] Показываем сохраненные результаты');
    
    // Загружаем сохраненные рекомендации
    const savedRecommendations = loadFromStorage(STORAGE_KEYS.RECOMMENDATIONS, []);
    
    if (savedRecommendations && savedRecommendations.length > 0) {
        console.log(`[Свайпы] Загружено ${savedRecommendations.length} сохраненных рекомендаций`);
        await showResultsOnSamePageWithData(savedRecommendations);
    } else {
        console.log('[Свайпы] Нет сохраненных рекомендаций, получаем новые');
        await showResultsOnSamePage();
    }
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
    
    // Переключатели типа контента
    const selectorTabs = document.querySelectorAll('.selector-tab');
    selectorTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const type = tab.dataset.type;
            switchContentType(type);
        });
    });
    
    // Кнопки управления
    const dislikeBtn = document.getElementById('dislikeBtn');
    const likeBtn = document.getElementById('likeBtn');
    const superlikeBtn = document.getElementById('superlikeBtn');
    const skipBtn = document.getElementById('skipBtn');
    const infoBtn = document.getElementById('cardInfoBtn');
    
    if (dislikeBtn) {
        dislikeBtn.addEventListener('click', () => handleSwipeAction('dislike'));
    }
    if (likeBtn) {
        likeBtn.addEventListener('click', () => handleSwipeAction('like'));
    }
    if (superlikeBtn) {
        superlikeBtn.addEventListener('click', () => handleSwipeAction('superlike'));
    }
    if (skipBtn) {
        skipBtn.addEventListener('click', () => handleSwipeAction('skip'));
    }
    if (infoBtn) {
        infoBtn.addEventListener('click', () => showCardInfo());
    }
    
    // Серендипити слайдер
    const serendipitySlider = document.getElementById('serendipitySlider');
    if (serendipitySlider) {
        serendipitySlider.addEventListener('input', (e) => {
            // Обновляем алгоритм рекомендаций на основе серендипити
            updateSerendipity(parseFloat(e.target.value));
        });
    }
    
    // Touch события для карточек
    setupTouchEvents();
    
    
    // Модальное окно
    const modalClose = document.getElementById('modalClose');
    if (modalClose) {
        modalClose.addEventListener('click', () => {
            hideModal();
        });
    }
}

// Переключение типа контента
function switchContentType(type) {
    currentSwipeType = type;
    
    // Обновляем активную вкладку
    const selectorTabs = document.querySelectorAll('.selector-tab');
    selectorTabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.type === type) {
            tab.classList.add('active');
        }
    });
    
    // Сбрасываем состояние и загружаем новые карточки
    currentCardIndex = 0;
    swipeCount = 0;
    loadCards();
}

// Загрузка карточек
async function loadCards() {
    try {
        // Если у нас уже есть карточки из localStorage, используем их
        if (currentCards && currentCards.length > 0) {
            console.log(`[Свайпы] Используем сохраненные карточки: ${currentCards.length}`);
            displayCurrentCard();
            updateProgress();
            return;
        }
        
        if (!sessionId) {
            // Создаем новую сессию
            const response = await fetch(`${swipeServiceUrl}/api/swipe/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    batch_size: totalSwipes
                })
            });
            
            if (!response.ok) {
                throw new Error('Ошибка создания сессии');
            }
            
            const data = await response.json();
            sessionId = data.session_id;
            currentCards = data.movies;
            
            // Сохраняем session ID и карточки
            saveToStorage(STORAGE_KEYS.SESSION_ID, sessionId);
            saveToStorage(STORAGE_KEYS.CURRENT_CARDS, currentCards);
        } else {
            // Получаем следующую партию карточек
            const response = await fetch(`${swipeServiceUrl}/api/swipe/next-batch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    batch_size: totalSwipes
                })
            });
            
            if (!response.ok) {
                throw new Error('Ошибка загрузки карточек');
            }
            
            const data = await response.json();
            currentCards = data.movies;
            
            // Сохраняем карточки
            saveToStorage(STORAGE_KEYS.CURRENT_CARDS, currentCards);
        }
        
        displayCurrentCard();
        updateProgress();
    } catch (error) {
        console.error('Ошибка загрузки карточек:', error);
        // Fallback к моковым данным
        const mockCards = generateMockCards(currentSwipeType);
        currentCards = mockCards;
        currentCardIndex = 0;
        swipeCount = 0;
        displayCurrentCard();
        updateProgress();
    }
}

// Генерация моковых карточек
function generateMockCards(type) {
    const baseCards = [
        {
            id: 1,
            title: 'Интерстеллар',
            description: 'Эпическая космическая драма о путешествии через червоточину',
            poster: 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=400&h=600&fit=crop',
            year: 2014,
            genre: 'Фантастика',
            rating: 8.6
        },
        {
            id: 2,
            title: 'Дюна',
            description: 'Эпическая фантастическая сага о пустынной планете Арракис',
            poster: 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop',
            year: 2021,
            genre: 'Фантастика',
            rating: 8.0
        },
        {
            id: 3,
            title: 'Топ Ган: Мэверик',
            description: 'Продолжение культового фильма о пилотах-истребителях',
            poster: 'https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=400&h=600&fit=crop',
            year: 2022,
            genre: 'Боевик',
            rating: 8.3
        },
        {
            id: 4,
            title: 'Бегущий по лезвию 2049',
            description: 'Продолжение культового фильма о репликантах в будущем',
            poster: 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop',
            year: 2017,
            genre: 'Фантастика',
            rating: 8.0
        },
        {
            id: 5,
            title: 'Матрица',
            description: 'Культовая фантастическая трилогия о виртуальной реальности',
            poster: 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=400&h=600&fit=crop',
            year: 1999,
            genre: 'Фантастика',
            rating: 8.7
        }
    ];
    
    // Возвращаем карточки в зависимости от типа
    return baseCards;
}

// Отображение текущей карточки
function displayCurrentCard() {
    const cardsStack = document.getElementById('cardsStack');
    cardsStack.innerHTML = '';
    
    // Показываем только текущую карточку
    if (currentCardIndex < currentCards.length) {
        const card = createSwipeCard(currentCards[currentCardIndex], 0);
        cardsStack.appendChild(card);
        
        // Анимация появления
        setTimeout(() => {
            card.classList.add('enter');
        }, 100);
    }
}

// Создание карточки для свайпа
function createSwipeCard(cardData, zIndex) {
    const card = document.createElement('div');
    card.className = 'swipe-card';
    card.dataset.cardId = cardData.id;
    card.style.zIndex = 10 - zIndex;
    
    card.innerHTML = `
        <div class="card-poster" style="background-image: url('${cardData.poster}')"></div>
        <div class="card-info">
            <div class="card-title">${cardData.title}</div>
            <div class="card-description">${cardData.description}</div>
            <div class="card-meta">
                <span class="card-year">${cardData.year}</span>
                <span class="card-genre">${cardData.genre}</span>
                <span class="card-rating">${cardData.rating}</span>
            </div>
        </div>
    `;
    
    return card;
}

// Настройка touch событий
function setupTouchEvents() {
    const cardsStack = document.getElementById('cardsStack');
    
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    let isDragging = false;
    
    // Touch события
    cardsStack.addEventListener('touchstart', handleTouchStart, { passive: false });
    cardsStack.addEventListener('touchmove', handleTouchMove, { passive: false });
    cardsStack.addEventListener('touchend', handleTouchEnd, { passive: false });
    
    // Mouse события
    cardsStack.addEventListener('mousedown', handleMouseDown);
    cardsStack.addEventListener('mousemove', handleMouseMove);
    cardsStack.addEventListener('mouseup', handleMouseUp);
    
    function handleTouchStart(e) {
        if (isAnimating || currentCardIndex >= currentCards.length) return;
        
        const touch = e.touches[0];
        startX = touch.clientX;
        startY = touch.clientY;
        isDragging = true;
        
        // Получаем текущую карточку
        currentCard = getCurrentCard();
        if (currentCard) {
            currentCard.classList.add('swiping');
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
            handleSwipeAction(action);
        } else {
            resetCardPosition();
        }
    }
    
    function handleMouseDown(e) {
        if (isAnimating || currentCardIndex >= currentCards.length) return;
        
        startX = e.clientX;
        startY = e.clientY;
        isDragging = true;
        
        // Получаем текущую карточку
        currentCard = getCurrentCard();
        if (currentCard) {
            currentCard.classList.add('swiping');
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
            handleSwipeAction(action);
        } else {
            resetCardPosition();
        }
    }
}

// Получение текущей карточки
function getCurrentCard() {
    const cards = document.querySelectorAll('.swipe-card');
    if (cards.length > 0) {
        return cards[0];
    }
    return null;
}

// Обновление позиции карточки
function updateCardPosition(deltaX, deltaY) {
    const currentCard = getCurrentCard();
    if (!currentCard) return;
    
    const rotation = deltaX * 0.1;
    const opacity = Math.max(0.3, 1 - Math.abs(deltaX) / 200);
    
    currentCard.style.transform = `translate(${deltaX}px, ${deltaY}px) rotate(${rotation}deg)`;
    currentCard.style.opacity = opacity;
}

// Обновление индикаторов свайпа
function updateSwipeIndicators(deltaX) {
    const currentCard = getCurrentCard();
    if (!currentCard) return;
    
    // Убираем все цветовые индикаторы
    currentCard.classList.remove('swipe-like', 'swipe-dislike', 'swipe-superlike');
    
    // Добавляем соответствующий цветовой индикатор
    if (deltaX > 50) {
        currentCard.classList.add('swipe-like');
    } else if (deltaX < -50) {
        currentCard.classList.add('swipe-dislike');
    }
}

// Сброс позиции карточки
function resetCardPosition() {
    const currentCard = getCurrentCard();
    if (!currentCard) return;
    
    currentCard.style.transform = '';
    currentCard.style.opacity = '';
    currentCard.classList.remove('swiping', 'swipe-like', 'swipe-dislike', 'swipe-superlike');
}

// Обработка действия свайпа
async function handleSwipeAction(action) {
    if (isAnimating || currentCardIndex >= currentCards.length) return;
    
    isAnimating = true;
    const currentCard = getCurrentCard();
    
    if (currentCard) {
        // Убираем все классы и inline стили
        currentCard.classList.remove('swipe-like', 'swipe-dislike', 'swipe-superlike', 'swiping');
        currentCard.style.transform = '';
        currentCard.style.opacity = '';
        
        // Добавляем класс анимации
        currentCard.classList.add(action);
        
        // Отправляем данные на сервер
        await sendSwipeAction(action, currentCards[currentCardIndex]);
        
        // Обновляем счетчики
        swipeCount++;
        currentCardIndex++;
        
        // Добавляем в историю свайпов
        swipeHistory.push({
            movie_id: currentCards[currentCardIndex - 1].id,
            action: action,
            timestamp: new Date().toISOString()
        });
        
        // Добавляем в соответствующий список
        if (action === 'like') {
            likedMovies.push(currentCards[currentCardIndex - 1].id);
        } else {
            dislikedMovies.push(currentCards[currentCardIndex - 1].id);
        }
        
        // Обновляем вектор пользователя локально
        updateUserVectorLocally(action, currentCards[currentCardIndex - 1]);
        
        // Сохраняем состояние в localStorage
        saveToStorage(STORAGE_KEYS.SWIPE_COUNT, swipeCount);
        saveToStorage(STORAGE_KEYS.CURRENT_CARD_INDEX, currentCardIndex);
        saveToStorage(STORAGE_KEYS.SWIPE_HISTORY, swipeHistory);
        saveToStorage(STORAGE_KEYS.LIKED_MOVIES, likedMovies);
        saveToStorage(STORAGE_KEYS.DISLIKED_MOVIES, dislikedMovies);
        saveToStorage(STORAGE_KEYS.USER_VECTOR, userVector);
        
        updateProgress();
        
        // Haptic feedback
        if ('vibrate' in navigator) {
            navigator.vibrate(50);
        }
        
        // Показываем следующую карточку после анимации
        setTimeout(() => {
            showNextCard();
            isAnimating = false;
        }, 500);
    }
}

// Отправка действия свайпа на сервер
async function sendSwipeAction(action, cardData) {
    if (!sessionId) {
        console.error('Сессия не создана');
        return;
    }
    
    try {
        const response = await fetch(`${swipeServiceUrl}/api/swipe/action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                movie_id: cardData.id,
                action: action
            })
        });
        
        if (!response.ok) {
            console.error('Ошибка отправки действия свайпа');
        } else {
            const data = await response.json();
            console.log('Свайп обработан:', data);
            
            // Обновляем вектор пользователя локально
            if (data.user_vector_norm !== undefined) {
                console.log('Норма вектора пользователя:', data.user_vector_norm);
                
                // Если сервер возвращает обновленный вектор, сохраняем его
                if (data.updated_profile) {
                    userVector = data.updated_profile;
                    saveToStorage(STORAGE_KEYS.USER_VECTOR, userVector);
                    console.log('[Свайпы] Сохранен обновленный вектор пользователя');
                }
            }
        }
    } catch (error) {
        console.error('Ошибка отправки действия свайпа:', error);
    }
}

// Показ следующей карточки
function showNextCard() {
    // Проверяем, нужно ли показать рекомендации
    if (swipeCount >= totalSwipes || currentCardIndex >= currentCards.length) {
        console.log(`[Свайпы] Свайпы завершены: ${swipeCount}/${totalSwipes}, карточка: ${currentCardIndex}/${currentCards.length}`);
        showResultsOnSamePage();
        return;
    }
    
    // Показываем следующую карточку
    displayCurrentCard();
}

// Обновление прогресса
function updateProgress() {
    const progressFill = document.getElementById('progressFill');
    const swipeCountEl = document.getElementById('swipeCount');
    const totalSwipesEl = document.getElementById('totalSwipes');
    
    if (progressFill) {
        const progress = (swipeCount / totalSwipes) * 100;
        progressFill.style.width = `${progress}%`;
    }
    
    if (swipeCountEl) {
        swipeCountEl.textContent = swipeCount;
    }
    if (totalSwipesEl) {
        totalSwipesEl.textContent = totalSwipes;
    }
}

// Показать рекомендации на той же странице
async function showResultsOnSamePage() {
    console.log('[Свайпы] Показываем рекомендации на той же странице');
    console.log(`[Свайпы] Текущее состояние: свайпов=${swipeCount}, карточек=${currentCards.length}, индекс=${currentCardIndex}`);
    
    try {
        // Получаем рекомендации от свайпов
        console.log('[Свайпы] Получаем рекомендации...');
        const recommendations = await getSwipeRecommendations();
        console.log(`[Свайпы] Получено рекомендаций: ${recommendations ? recommendations.length : 0}`);
        
        if (recommendations && recommendations.length > 0) {
            // Сохраняем рекомендации в localStorage
            saveToStorage(STORAGE_KEYS.RECOMMENDATIONS, recommendations);
            saveToStorage(STORAGE_KEYS.SHOW_RESULTS, true);
            console.log(`[Свайпы] Сохранено ${recommendations.length} рекомендаций в localStorage`);
            
            await showResultsOnSamePageWithData(recommendations);
        } else {
            console.error('Не удалось получить рекомендации');
            showErrorMessage('Не удалось получить рекомендации. Попробуйте еще раз.');
        }
    } catch (error) {
        console.error('Ошибка при получении рекомендаций:', error);
        showErrorMessage('Ошибка при получении рекомендаций');
    }
}

// Показать результаты с готовыми данными
async function showResultsOnSamePageWithData(recommendations) {
    console.log(`Показываем ${recommendations.length} рекомендаций`);
    
    try {
        // Скрываем контейнер свайпов
        const swipeContainer = document.querySelector('.swipe-container');
        const swipeControls = document.querySelector('.swipe-controls');
        const swipeProgress = document.querySelector('.swipe-progress');
        
        if (swipeContainer) swipeContainer.style.display = 'none';
        if (swipeControls) swipeControls.style.display = 'none';
        if (swipeProgress) swipeProgress.style.display = 'none';
        
        // Создаем контейнер для результатов
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'results-container';
        
        // Заголовок
        const header = document.createElement('div');
        header.style.cssText = `
            text-align: center;
            margin-bottom: 24px;
        `;
        header.innerHTML = `
            <h3 style="color: var(--okko-text); font-size: 24px; font-weight: 600; margin: 0 0 8px 0;">
                💫 Ваши рекомендации готовы!
            </h3>
            <p style="color: var(--okko-text-muted); font-size: 16px; margin: 0;">
                Мы изучили ваши предпочтения на основе ${swipeCount} свайпов
            </p>
        `;
        resultsContainer.appendChild(header);
        
        // Сетка фильмов
        const moviesGrid = document.createElement('div');
        moviesGrid.className = 'movies-grid';
        
        // Добавляем фильмы
        recommendations.forEach((movie, index) => {
            const movieCard = createMovieCard(movie, index);
            moviesGrid.appendChild(movieCard);
        });
        
        resultsContainer.appendChild(moviesGrid);
        
        // Кнопки действий
        const actionsContainer = document.createElement('div');
        actionsContainer.style.cssText = `
            display: flex;
            justify-content: center;
            gap: 16px;
            flex-wrap: wrap;
        `;
        
        actionsContainer.innerHTML = `
            <button class="action-btn primary-btn" id="viewResultsBtn" style="
                background: var(--okko-accent);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <i class="fas fa-star"></i>
                Подробные результаты
            </button>
            <button class="action-btn secondary-btn" id="restartFromResultsBtn" style="
                background: var(--okko-surface-2);
                color: var(--okko-text);
                border: 1px solid var(--okko-border);
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 500;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <i class="fas fa-redo"></i>
                Начать заново
            </button>
        `;
        
        resultsContainer.appendChild(actionsContainer);
        
        // Добавляем контейнер на страницу
        const mainContent = document.querySelector('.main-content') || document.querySelector('.app-container');
        if (mainContent) {
            mainContent.appendChild(resultsContainer);
        }
        
        // Обработчики кнопок
        const viewResultsBtn = document.getElementById('viewResultsBtn');
        const restartFromResultsBtn = document.getElementById('restartFromResultsBtn');
        
        if (viewResultsBtn) {
            viewResultsBtn.addEventListener('click', () => {
                // Сохраняем рекомендации и переходим на страницу результатов
                localStorage.setItem('swipeRecommendations', JSON.stringify(recommendations));
                localStorage.setItem('userProfile', JSON.stringify({
                    swipe_count: swipeCount,
                    liked_count: 0, // Будет обновлено при получении профиля
                    disliked_count: 0 // Будет обновлено при получении профиля
                }));
                window.location.href = '/results';
            });
        }
        
        if (restartFromResultsBtn) {
            restartFromResultsBtn.addEventListener('click', () => {
                // Перезапускаем свайпы
                restartSwipes();
            });
        }
        
        console.log(`Показано ${recommendations.length} рекомендаций на той же странице`);
    } catch (error) {
        console.error('Ошибка при показе результатов:', error);
        showErrorMessage('Ошибка при показе результатов');
    }
}

// Создание карточки фильма для результатов
function createMovieCard(movie, index) {
    const card = document.createElement('div');
    card.style.cssText = `
        background: var(--okko-surface-2);
        border: 1px solid var(--okko-border);
        border-radius: 12px;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        cursor: pointer;
        height: fit-content;
    `;
    
    card.innerHTML = `
        <div style="
            background-image: url('${movie.poster}');
            background-size: cover;
            background-position: center;
            height: 150px;
            position: relative;
        ">
            <div style="
                position: absolute;
                top: 8px;
                right: 8px;
                background: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            ">
                ${movie.rating}
            </div>
        </div>
        <div style="padding: 16px;">
            <h4 style="
                color: var(--okko-text);
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 8px 0;
                line-height: 1.3;
            ">
                ${movie.title}
            </h4>
            <div style="
                color: var(--okko-text-muted);
                font-size: 14px;
                margin-bottom: 8px;
            ">
                ${movie.year} • ${movie.genre} • ${movie.duration} мин
            </div>
            <p style="
                color: var(--okko-text-muted);
                font-size: 13px;
                line-height: 1.4;
                margin: 0;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            ">
                ${movie.description}
            </p>
            ${movie.reason ? `
                <div style="
                    margin-top: 8px;
                    padding: 6px 8px;
                    background: var(--okko-accent-light);
                    border-radius: 4px;
                    font-size: 12px;
                    color: var(--okko-accent);
                ">
                    ${movie.reason}
                </div>
            ` : ''}
        </div>
    `;
    
    // Hover эффект
    card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-4px)';
        card.style.boxShadow = '0 8px 20px rgba(0, 0, 0, 0.15)';
    });
    
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0)';
        card.style.boxShadow = 'none';
    });
    
    return card;
}

// Показать сообщение об ошибке
function showErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--okko-danger);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 1000;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    `;
    errorDiv.textContent = message;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 3000);
}

// Получить профиль пользователя
async function getUserProfile() {
    if (!sessionId) return;
    
    try {
        const response = await fetch(`${swipeServiceUrl}/api/swipe/profile`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Профиль пользователя:', data);
            
            // Сохраняем профиль в localStorage для использования на странице результатов
            localStorage.setItem('userProfile', JSON.stringify(data));
        }
    } catch (error) {
        console.error('Ошибка получения профиля:', error);
    }
}

// Получить рекомендации на основе свайпов
async function getSwipeRecommendations() {
    // Сначала пытаемся получить рекомендации с сервера
    if (sessionId) {
        try {
            const response = await fetch(`${swipeServiceUrl}/api/swipe/recommendations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    top_k: 6
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.recommendations;
            }
        } catch (error) {
            console.error('Ошибка получения рекомендаций с сервера:', error);
        }
    }
    
    // Если сервер недоступен, используем локальные данные
    return getLocalRecommendations();
}

// Получить локальные рекомендации на основе истории свайпов
function getLocalRecommendations() {
    console.log('[Свайпы] Получаем локальные рекомендации');
    console.log(`[Свайпы] История свайпов: ${swipeHistory.length}, лайков: ${likedMovies.length}, дизлайков: ${dislikedMovies.length}`);
    
    // Если нет истории свайпов, возвращаем пустой массив
    if (swipeHistory.length === 0) {
        console.log('[Свайпы] Нет истории свайпов, возвращаем пустой массив');
        return [];
    }
    
    // Создаем простые рекомендации на основе лайкнутых фильмов
    const recommendations = [];
    const likedMovieIds = likedMovies.slice(-5); // Берем последние 5 лайкнутых
    
    // Генерируем рекомендации на основе лайкнутых фильмов
    likedMovieIds.forEach((movieId, index) => {
        const movie = currentCards.find(card => card.id === movieId);
        if (movie) {
            recommendations.push({
                ...movie,
                similarity: 0.8 - (index * 0.1), // Убывающее сходство
                reason: `Похож на ${movie.title}`
            });
        }
    });
    
    // Если рекомендаций мало, добавляем случайные фильмы
    if (recommendations.length < 6) {
        const remaining = 6 - recommendations.length;
        const usedIds = new Set(likedMovieIds);
        const availableMovies = currentCards.filter(card => !usedIds.has(card.id));
        
        for (let i = 0; i < Math.min(remaining, availableMovies.length); i++) {
            const movie = availableMovies[i];
            recommendations.push({
                ...movie,
                similarity: 0.5 - (i * 0.05),
                reason: 'Рекомендация на основе ваших предпочтений'
            });
        }
    }
    
    const finalRecommendations = recommendations.slice(0, 6);
    console.log(`[Свайпы] Создано ${finalRecommendations.length} локальных рекомендаций`);
    return finalRecommendations;
}


// Показать информацию о карточке
function showCardInfo() {
    if (currentCardIndex >= currentCards.length) return;
    
    const cardData = currentCards[currentCardIndex];
    
    if (cardData) {
        const modal = document.getElementById('cardModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        
        if (modal && modalTitle && modalBody) {
            modalTitle.textContent = cardData.title;
            modalBody.innerHTML = `
                <div class="movie-details">
                    <div class="movie-poster" style="background-image: url('${cardData.poster}')"></div>
                    <div class="movie-info">
                        <div class="movie-year">${cardData.year}</div>
                        <div class="movie-genre">${cardData.genre}</div>
                        <div class="movie-rating">Рейтинг: ${cardData.rating}</div>
                        <div class="movie-description">${cardData.description}</div>
                    </div>
                </div>
            `;
            modal.classList.add('active');
        }
    }
}

// Скрыть модальное окно
function hideModal() {
    const modal = document.getElementById('cardModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Обновление серендипити
function updateSerendipity(value) {
    // Здесь можно обновить алгоритм рекомендаций
    console.log('Серендипити обновлен:', value);
}

// Функция для тестирования характеристик фильма
async function testMovieFeatures(movieId) {
    try {
        const response = await fetch(`${swipeServiceUrl}/api/swipe/debug/movie/${movieId}`);
        if (response.ok) {
            const data = await response.json();
            console.log('Тест характеристик фильма:', data);
            return data;
        }
    } catch (error) {
        console.error('Ошибка тестирования характеристик:', error);
    }
}

// Добавляем глобальную функцию для тестирования
window.testMovieFeatures = testMovieFeatures;

// Локальное обновление вектора пользователя
function updateUserVectorLocally(action, movie) {
    console.log(`[Свайпы] Обновляем вектор пользователя локально: ${action} для ${movie.title}`);
    
    // Инициализируем вектор пользователя, если его нет
    if (!userVector) {
        userVector = new Array(384).fill(0); // 384 - размер вектора sentence-transformers
        console.log('[Свайпы] Инициализирован новый вектор пользователя');
    }
    
    // Создаем простой вектор фильма на основе его характеристик
    const movieVector = createMovieVector(movie);
    
    // Определяем вес в зависимости от действия
    const weight = action === 'like' ? 0.1 : -0.1;
    
    // Обновляем вектор пользователя
    for (let i = 0; i < userVector.length; i++) {
        userVector[i] += weight * movieVector[i];
    }
    
    // Нормализуем вектор
    const norm = Math.sqrt(userVector.reduce((sum, val) => sum + val * val, 0));
    if (norm > 0) {
        for (let i = 0; i < userVector.length; i++) {
            userVector[i] /= norm;
        }
    }
    
    console.log(`[Свайпы] Вектор пользователя обновлен, норма: ${norm.toFixed(3)}`);
}

// Создание простого вектора фильма на основе его характеристик
function createMovieVector(movie) {
    const vector = new Array(384).fill(0);
    
    // Используем характеристики фильма для создания вектора
    const title = movie.title.toLowerCase();
    const genre = movie.genre.toLowerCase();
    const description = movie.description.toLowerCase();
    
    // Простая хеш-функция для создания вектора
    let hash = 0;
    const text = `${title} ${genre} ${description}`;
    
    for (let i = 0; i < text.length; i++) {
        hash = ((hash << 5) - hash + text.charCodeAt(i)) & 0xffffffff;
    }
    
    // Заполняем вектор на основе хеша
    for (let i = 0; i < vector.length; i++) {
        vector[i] = Math.sin(hash + i) * 0.1;
    }
    
    return vector;
}

// Перезапуск свайпов
function restartSwipes() {
    console.log('[Свайпы] Перезапуск свайпов - сброс всех параметров');
    
    // Очищаем localStorage
    clearStorage();
    
    // Сбрасываем флаг показа результатов
    saveToStorage(STORAGE_KEYS.SHOW_RESULTS, false);
    
    // Сбрасываем все глобальные переменные
    currentCards = [];
    currentCardIndex = 0;
    swipeCount = 0;
    isAnimating = false;
    currentCard = null;
    sessionId = null;
    userVector = null;
    swipeHistory = [];
    likedMovies = [];
    dislikedMovies = [];
    
    // Перезагружаем страницу
    location.reload();
}
