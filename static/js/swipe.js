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

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeSwipe();
});

// Основная инициализация
function initializeSwipe() {
    if (isInitialized) return;
    
    hideLoadingScreen();
    setupEventListeners();
    loadCards();
    updateProgress();
    isInitialized = true;
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
    
    // Кнопки завершения
    const showResultsBtn = document.getElementById('showResultsBtn');
    const continueSwipingBtn = document.getElementById('continueSwipingBtn');
    
    if (showResultsBtn) {
        showResultsBtn.addEventListener('click', () => {
            window.location.href = '/results';
        });
    }
    if (continueSwipingBtn) {
        continueSwipingBtn.addEventListener('click', () => {
            hideCompletionScreen();
            // Сбрасываем состояние и загружаем новые карточки
            currentCardIndex = 0;
            swipeCount = 0;
            loadCards();
        });
    }
    
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
        // Имитация загрузки карточек
        const mockCards = generateMockCards(currentSwipeType);
        currentCards = mockCards;
        currentCardIndex = 0;
        swipeCount = 0;
        
        displayCurrentCard();
        updateProgress();
    } catch (error) {
        console.error('Ошибка загрузки карточек:', error);
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
    try {
        const response = await fetch('/api/swipe/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: action,
                content: cardData,
                type: currentSwipeType
            })
        });
        
        if (!response.ok) {
            console.error('Ошибка отправки действия свайпа');
        }
    } catch (error) {
        console.error('Ошибка отправки действия свайпа:', error);
    }
}

// Показ следующей карточки
function showNextCard() {
    // Проверяем, нужно ли показать экран завершения
    if (swipeCount >= totalSwipes || currentCardIndex >= currentCards.length) {
        showCompletionScreen();
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

// Показать экран завершения
function showCompletionScreen() {
    const completionScreen = document.getElementById('completionScreen');
    if (completionScreen) {
        completionScreen.style.display = 'flex';
        
        // Обновляем текст завершения
        const completionText = document.getElementById('completionText');
        if (completionText) {
            completionText.textContent = `Мы изучили ваши предпочтения на основе ${swipeCount} свайпов и готовы предложить персонализированные рекомендации`;
        }
    }
}

// Скрыть экран завершения
function hideCompletionScreen() {
    const completionScreen = document.getElementById('completionScreen');
    if (completionScreen) {
        completionScreen.style.display = 'none';
    }
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
