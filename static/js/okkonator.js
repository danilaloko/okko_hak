/* ==============================
   Okkonator - Экран вопросов и ответов
   ============================== */

// Глобальные переменные
let currentQuestion = null;
let questionIndex = 0;
let confidence = 0;
let isProcessing = false;
let askedQuestions = []; // Массив заданных вопросов
let userProfile = {}; // Профиль пользователя
let firstRecommendationsShown = false; // Были ли показаны первые рекомендации при 70%
// Убрано кэширование рекомендаций - всегда запрашиваем свежие данные

// Ключи для localStorage
const STORAGE_KEYS = {
    PROFILE: 'okkonator_profile',
    ANSWERS: 'okkonator_answers',
    CONFIDENCE: 'okkonator_confidence',
    ASKED_QUESTIONS: 'okkonator_asked_questions',
    FIRST_RECOMMENDATIONS_SHOWN: 'okkonator_first_recommendations_shown'
};

// Функции логгирования
function log(message, data = null) {
    console.log(`[Окконатор] ${message}`, data || '');
}

function logError(message, error = null) {
    console.error(`[Окконатор ОШИБКА] ${message}`, error || '');
}

function logSuccess(message, data = null) {
    console.log(`[Окконатор УСПЕХ] ${message}`, data || '');
}

// Функции для работы с localStorage
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        log(`Сохранено в localStorage: ${key}`, data);
    } catch (error) {
        logError(`Ошибка сохранения в localStorage: ${key}`, error);
    }
}

function loadFromStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(key);
        if (data) {
            const parsed = JSON.parse(data);
            log(`Загружено из localStorage: ${key}`, parsed);
            return parsed;
        }
    } catch (error) {
        logError(`Ошибка загрузки из localStorage: ${key}`, error);
    }
    return defaultValue;
}

function clearStorage() {
    try {
        Object.values(STORAGE_KEYS).forEach(key => {
            localStorage.removeItem(key);
        });
        log('Очищен localStorage Окконатора');
    } catch (error) {
        logError('Ошибка очистки localStorage', error);
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    log('Инициализация Окконатора');
    initializeOkkonator();
});

// Основная инициализация
function initializeOkkonator() {
    hideLoadingScreen();
    setupEventListeners();
    loadUserData();
    loadNextQuestion();
}

// Загрузка данных пользователя из localStorage
function loadUserData() {
    log('Загружаем данные пользователя из localStorage');
    
    // Загружаем профиль
    userProfile = loadFromStorage(STORAGE_KEYS.PROFILE, {});
    
    // Загружаем ответы
    const savedAnswers = loadFromStorage(STORAGE_KEYS.ANSWERS, []);
    askedQuestions = savedAnswers.map(answer => answer.question_id);
    
    // Загружаем уверенность
    confidence = loadFromStorage(STORAGE_KEYS.CONFIDENCE, 0);
    
    // Загружаем флаг показа первых рекомендаций
    firstRecommendationsShown = loadFromStorage(STORAGE_KEYS.FIRST_RECOMMENDATIONS_SHOWN, false);
    
    log(`Загружены данные: профиль=${Object.keys(userProfile).length} осей, ответов=${askedQuestions.length}, уверенность=${confidence}%, первые рекомендации показаны=${firstRecommendationsShown}`);
    
    // Обновляем индикатор уверенности
    updateConfidence();
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
    
    // Кнопка чата
    const chatBtn = document.getElementById('chatBtn');
    if (chatBtn) {
        chatBtn.addEventListener('click', () => {
            window.location.href = '/chat';
        });
    }
    
    // Кнопки ответов
    const answerBtns = document.querySelectorAll('.answer-btn');
    answerBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const answer = btn.dataset.answer;
            handleAnswer(answer);
        });
    });
    
    // Уточняющие чипы
    const chips = document.querySelectorAll('.chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const filter = chip.dataset.filter;
            handleClarification(filter);
        });
    });
    
    // Кнопки угаданного кандидата
    const watchBtn = document.getElementById('watchBtn');
    const wrongBtn = document.getElementById('wrongBtn');
    
    if (watchBtn) {
        watchBtn.addEventListener('click', () => {
            handleWatchMovie();
        });
    }
    if (wrongBtn) {
        wrongBtn.addEventListener('click', () => {
            handleGuessResponse(false);
        });
    }
    
    // Кнопки действий
    const continueBtn = document.getElementById('continueBtn');
    const showResultsBtn = document.getElementById('showResultsBtn');
    const goToChatBtn = document.getElementById('goToChatBtn');
    
    if (continueBtn) {
        continueBtn.addEventListener('click', () => {
            loadNextQuestion();
        });
    }
    if (showResultsBtn) {
        showResultsBtn.addEventListener('click', async () => {
            log('Нажата кнопка "Показать результаты"');
            // Получаем рекомендации перед переходом
            const recommendations = await getOkkonatorRecommendations();
            if (recommendations.length > 0) {
                logSuccess(`Сохранено ${recommendations.length} рекомендаций в localStorage`);
                // Сохраняем рекомендации в localStorage для передачи на страницу результатов
                localStorage.setItem('okkonator_recommendations', JSON.stringify(recommendations));
                localStorage.setItem('okkonator_profile', JSON.stringify(userProfile));
            window.location.href = '/results';
            } else {
                logError('Не удалось получить рекомендации');
                showErrorMessage('Не удалось получить рекомендации. Попробуйте еще раз.');
            }
        });
    }
    if (goToChatBtn) {
        goToChatBtn.addEventListener('click', () => {
            window.location.href = '/chat';
        });
    }
}

// Загрузка следующего вопроса
async function loadNextQuestion() {
    if (isProcessing) {
        log('Пропускаем загрузку - уже обрабатывается');
        return;
    }
    
    try {
        log('Загружаем следующий вопрос');
        showLoadingScreen('Загружаем вопрос...');
        
        // Передаем данные из localStorage
        const requestData = {
            theta: userProfile,
            asked_ids: askedQuestions
        };
        
        log('Отправляем данные в сервис:', requestData);
        
        const response = await fetch('/api/okkonator/question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        const data = await response.json();
        
        log('Получен ответ от сервера:', data);
        
        if (data.error) {
            logError('Ошибка сервиса:', data.error);
            showErrorMessage(data.error);
            hideLoadingScreen();
            return;
        }
        
        if (data.question) {
            currentQuestion = data.question;
            questionIndex = data.question.id;
            confidence = data.confidence || 0;
            
            // Сохраняем уверенность в localStorage
            saveToStorage(STORAGE_KEYS.CONFIDENCE, confidence);
            
            log(`Загружен вопрос: ${data.question.text} (ID: ${data.question.id})`);
            log(`Уверенность: ${confidence}%`);
            
            // Проверяем уверенность после получения данных от сервера
            if (confidence >= 70 && confidence < 100 && !firstRecommendationsShown) {
                log('Уверенность достигла 70%, показываем первую подборку');
                firstRecommendationsShown = true;
                saveToStorage(STORAGE_KEYS.FIRST_RECOMMENDATIONS_SHOWN, firstRecommendationsShown);
                hideLoadingScreen();
                showGuessedCandidate();
            } else if (confidence >= 100) {
                log('Уверенность достигла 100%, показываем окончательную подборку');
                hideLoadingScreen();
                showFinalRecommendations();
            } else {
                log('Продолжаем с вопросами, уверенность:', confidence);
            displayQuestion();
            updateConfidence();
            hideLoadingScreen();
            }
        } else if (data.message && data.message.includes('закончились')) {
            log('Вопросы закончились, проверяем уверенность для показа рекомендаций');
            
            // Проверяем уверенность при завершении вопросов
            if (confidence >= 70 && confidence < 100 && !firstRecommendationsShown) {
                log('Уверенность 70-99%, показываем первую подборку');
                firstRecommendationsShown = true;
                saveToStorage(STORAGE_KEYS.FIRST_RECOMMENDATIONS_SHOWN, firstRecommendationsShown);
                hideLoadingScreen();
                showGuessedCandidate();
            } else if (confidence >= 100) {
                log('Уверенность 100%, показываем окончательную подборку');
                hideLoadingScreen();
                showFinalRecommendations();
            } else {
                log('Уверенность < 70%, показываем результаты на той же странице');
                hideLoadingScreen();
                showResultsOnSamePage();
            }
        } else {
            log('Неожиданный ответ сервера:', data);
            showErrorMessage('Неожиданный ответ сервера');
            hideLoadingScreen();
        }
    } catch (error) {
        logError('Ошибка загрузки вопроса:', error);
        showErrorMessage('Ошибка подключения к сервису');
        hideLoadingScreen();
    }
}

// Отображение вопроса
function displayQuestion() {
    const questionText = document.getElementById('questionText');
    if (questionText && currentQuestion) {
        questionText.textContent = currentQuestion.text;
    }
    
    // Скрываем угаданного кандидата
    const guessContainer = document.getElementById('guessContainer');
    if (guessContainer) {
        guessContainer.style.display = 'none';
    }
    
    // Показываем кнопки действий
    const continueBtn = document.getElementById('continueBtn');
    const showResultsBtn = document.getElementById('showResultsBtn');
    const goToChatBtn = document.getElementById('goToChatBtn');
    
    if (continueBtn) continueBtn.style.display = 'none';
    if (showResultsBtn) showResultsBtn.style.display = 'none';
    if (goToChatBtn) goToChatBtn.style.display = 'none';
}

// Обработка ответа
async function handleAnswer(answer) {
    if (isProcessing) {
        log('Пропускаем обработку ответа - уже обрабатывается');
        return;
    }
    
    isProcessing = true;
    log(`Обрабатываем ответ: ${answer} для вопроса ${questionIndex}`);
    
    // Показываем загрузочный экран сразу после нажатия
    showLoadingScreen('Обрабатываем ответ...', 'Анализируем ваши предпочтения');
    
    try {
        // Отправляем ответ на сервер
        const response = await fetch('/api/okkonator/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                answer: answer,
                question_id: questionIndex,
                theta: userProfile,
                asked_ids: askedQuestions
            })
        });
        
        const data = await response.json();
        log('Получен ответ от сервера:', data);
        
        if (response.ok && data.success) {
            logSuccess('Ответ успешно обработан');
            
            // Сохраняем профиль пользователя
            if (data.theta) {
                userProfile = data.theta;
                saveToStorage(STORAGE_KEYS.PROFILE, userProfile);
                log('Обновлен профиль пользователя:', userProfile);
            }
            
            // Сохраняем ответ
            const answerData = {
                question_id: questionIndex,
                answer: answer
            };
            const savedAnswers = loadFromStorage(STORAGE_KEYS.ANSWERS, []);
            savedAnswers.push(answerData);
            saveToStorage(STORAGE_KEYS.ANSWERS, savedAnswers);
            askedQuestions.push(questionIndex);
            
            // Получаем уверенность от сервера (если есть)
            if (data.confidence !== undefined) {
                confidence = data.confidence;
                saveToStorage(STORAGE_KEYS.CONFIDENCE, confidence);
                log(`Уверенность от сервера: ${confidence}%`);
            } else {
                // Если уверенность не пришла от сервера, сохраняем текущую
                saveToStorage(STORAGE_KEYS.CONFIDENCE, confidence);
            }
            
            updateConfidence();
            
            // Сбрасываем флаг обработки и загружаем следующий вопрос
            // Проверка уверенности произойдет в loadNextQuestion после получения данных от сервера
            isProcessing = false;
                setTimeout(() => {
                    loadNextQuestion();
            }, 1000);
        } else {
            logError('Ошибка обработки ответа:', data.error);
            hideLoadingScreen();
            showErrorMessage(data.error || 'Ошибка обработки ответа');
                    isProcessing = false;
        }
    } catch (error) {
        logError('Ошибка отправки ответа:', error);
        hideLoadingScreen();
        showErrorMessage('Ошибка подключения к сервису');
        isProcessing = false;
    }
}

// Обновление индикатора уверенности
function updateConfidence() {
    const confidenceFill = document.getElementById('confidenceFill');
    const confidenceValue = document.getElementById('confidenceValue');
    
    if (confidenceFill) {
        confidenceFill.style.width = `${confidence}%`;
    }
    if (confidenceValue) {
        confidenceValue.textContent = `${confidence}%`;
    }
}

// Показать угаданного кандидата
async function showGuessedCandidate() {
    log('Показываем угаданного кандидата, получаем рекомендации от Окконатора');
    
    try {
        // Получаем рекомендации от Окконатора
        const recommendations = await getOkkonatorRecommendations();
        
        if (recommendations.length > 0) {
            // Берем первые 3 рекомендации
            const topCandidates = recommendations.slice(0, 3);
            logSuccess(`Получено ${topCandidates.length} угаданных кандидатов`);
            
            const guessContainer = document.getElementById('guessContainer');
            
            if (guessContainer) {
                // Очищаем контейнер
                guessContainer.innerHTML = '';
                
                // Создаем заголовок
                const header = document.createElement('div');
                header.className = 'guess-header';
                header.innerHTML = `
                    <h3>🎬 Первая подборка готова!</h3>
                    <p>Мы уже понимаем ваши предпочтения. Вот предварительная подборка:</p>
                `;
                guessContainer.appendChild(header);
                
                // Создаем сетку для 3 фильмов
                const moviesGrid = document.createElement('div');
                moviesGrid.className = 'guess-movies-grid';
                moviesGrid.style.cssText = `
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                `;
                
                topCandidates.forEach((candidate, index) => {
                    const movieCard = document.createElement('div');
                    movieCard.className = 'guess-movie-card';
                    movieCard.style.cssText = `
                        background: white;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        transition: transform 0.3s ease;
                    `;
                    
                    movieCard.innerHTML = `
                        <div class="guess-movie-poster" style="
                            height: 200px;
                            background-image: url('${candidate.poster || 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop'}');
                            background-size: cover;
                            background-position: center;
                            position: relative;
                        ">
                            <div style="
                                position: absolute;
                                top: 10px;
                                right: 10px;
                                background: rgba(0,0,0,0.7);
                                color: white;
                                padding: 4px 8px;
                                border-radius: 4px;
                                font-size: 12px;
                            ">${candidate.rating || 'N/A'}</div>
                        </div>
                        <div style="padding: 15px;">
                            <h4 style="margin: 0 0 5px 0; font-size: 16px; color: #333;">${candidate.title}</h4>
                            <p style="margin: 0 0 5px 0; font-size: 14px; color: #666;">${candidate.year} • ${candidate.duration || 'N/A'} мин</p>
                            <p style="margin: 0 0 10px 0; font-size: 12px; color: #888;">${candidate.genre || 'Жанр не указан'}</p>
                            ${candidate.reason ? `<p style="margin: 0; font-size: 11px; color: #999; font-style: italic;">${candidate.reason}</p>` : ''}
                        </div>
                    `;
                    
                    // Добавляем эффект при наведении
                    movieCard.addEventListener('mouseenter', () => {
                        movieCard.style.transform = 'translateY(-5px)';
                    });
                    movieCard.addEventListener('mouseleave', () => {
                        movieCard.style.transform = 'translateY(0)';
                    });
                    
                    moviesGrid.appendChild(movieCard);
                });
                
                guessContainer.appendChild(moviesGrid);
                
                // Создаем кнопки действий
                const actionsContainer = document.createElement('div');
                actionsContainer.className = 'guess-actions';
                actionsContainer.style.cssText = `
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    margin-top: 20px;
                `;
                
                actionsContainer.innerHTML = `
                    <button class="guess-btn watch-btn" id="watchBtn" style="
                        background: var(--okko-primary);
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
                        <i class="fas fa-play"></i>
                        Смотреть рекомендации
                    </button>
                    <button class="guess-btn no-btn" id="wrongBtn" style="
                        background: #f5f5f5;
                        color: #666;
                        border: 1px solid #ddd;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-weight: 500;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    ">
                        <i class="fas fa-forward"></i>
                        Продолжить вопросы
                    </button>
                    <button class="guess-btn restart-btn" id="restartFromGuessBtn" style="
                        background: #f8f9fa;
                        color: #6c757d;
                        border: 1px solid #dee2e6;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-weight: 500;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    ">
                        <i class="fas fa-redo"></i>
                        Начать сначала
                    </button>
                `;
                
                guessContainer.appendChild(actionsContainer);
                
                // Переподключаем обработчики событий
                const watchBtn = document.getElementById('watchBtn');
                const wrongBtn = document.getElementById('wrongBtn');
                const restartFromGuessBtn = document.getElementById('restartFromGuessBtn');
                
                if (watchBtn) {
                    watchBtn.addEventListener('click', handleWatchMovie);
                }
                if (wrongBtn) {
                    wrongBtn.addEventListener('click', () => handleGuessResponse(false));
                }
                if (restartFromGuessBtn) {
                    restartFromGuessBtn.addEventListener('click', restartOkkonator);
                }
                
                guessContainer.style.display = 'block';
            }
        } else {
            logError('Не удалось получить рекомендации для угаданного кандидата');
            showErrorMessage('Не удалось получить рекомендации');
        }
    } catch (error) {
        logError('Ошибка при получении угаданного кандидата:', error);
        showErrorMessage('Ошибка получения рекомендаций');
    }
    
    isProcessing = false;
}

// Показать окончательные рекомендации (при 100% уверенности)
async function showFinalRecommendations() {
    log('Показываем окончательные рекомендации при 100% уверенности');
    
    try {
        // Получаем рекомендации от Окконатора
        const recommendations = await getOkkonatorRecommendations();
        
        if (recommendations.length > 0) {
            // Берем первые 3 рекомендации
            const topCandidates = recommendations.slice(0, 3);
            logSuccess(`Получено ${topCandidates.length} окончательных рекомендаций`);
            
            const guessContainer = document.getElementById('guessContainer');
            
            if (guessContainer) {
                // Очищаем контейнер
                guessContainer.innerHTML = '';
                
                // Создаем заголовок для окончательных рекомендаций
                const header = document.createElement('div');
                header.className = 'guess-header';
                header.innerHTML = `
                    <h3>🎯 Ваша идеальная подборка готова!</h3>
                    <p>Мы изучили все ваши предпочтения и подобрали идеальные фильмы:</p>
                `;
                guessContainer.appendChild(header);
                
                // Создаем сетку для 3 фильмов
                const moviesGrid = document.createElement('div');
                moviesGrid.className = 'guess-movies-grid';
                moviesGrid.style.cssText = `
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                `;
                
                topCandidates.forEach((candidate, index) => {
                    const movieCard = document.createElement('div');
                    movieCard.className = 'guess-movie-card';
                    movieCard.style.cssText = `
                        background: white;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        transition: transform 0.3s ease;
                    `;
                    
                    movieCard.innerHTML = `
                        <div class="guess-movie-poster" style="
                            height: 200px;
                            background-image: url('${candidate.poster || 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop'}');
                            background-size: cover;
                            background-position: center;
                            position: relative;
                        ">
                            <div style="
                                position: absolute;
                                top: 10px;
                                right: 10px;
                                background: rgba(0,0,0,0.7);
                                color: white;
                                padding: 4px 8px;
                                border-radius: 4px;
                                font-size: 12px;
                            ">${candidate.rating || 'N/A'}</div>
                        </div>
                        <div style="padding: 15px;">
                            <h4 style="margin: 0 0 5px 0; font-size: 16px; color: #333;">${candidate.title}</h4>
                            <p style="margin: 0 0 5px 0; font-size: 14px; color: #666;">${candidate.year} • ${candidate.duration || 'N/A'} мин</p>
                            <p style="margin: 0 0 10px 0; font-size: 12px; color: #888;">${candidate.genre || 'Жанр не указан'}</p>
                            ${candidate.reason ? `<p style="margin: 0; font-size: 11px; color: #999; font-style: italic;">${candidate.reason}</p>` : ''}
                        </div>
                    `;
                    
                    // Добавляем эффект при наведении
                    movieCard.addEventListener('mouseenter', () => {
                        movieCard.style.transform = 'translateY(-5px)';
                    });
                    movieCard.addEventListener('mouseleave', () => {
                        movieCard.style.transform = 'translateY(0)';
                    });
                    
                    moviesGrid.appendChild(movieCard);
                });
                
                guessContainer.appendChild(moviesGrid);
                
                // Создаем кнопки действий для окончательных рекомендаций
                const actionsContainer = document.createElement('div');
                actionsContainer.className = 'guess-actions';
                actionsContainer.style.cssText = `
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    margin-top: 20px;
                `;
                
                actionsContainer.innerHTML = `
                    <button class="guess-btn watch-btn" id="finalWatchBtn" style="
                        background: var(--okko-primary);
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
                        <i class="fas fa-play"></i>
                        Смотреть рекомендации
                    </button>
                    <button class="guess-btn restart-btn" id="finalRestartBtn" style="
                        background: #f8f9fa;
                        color: #6c757d;
                        border: 1px solid #dee2e6;
                        padding: 12px 24px;
                        border-radius: 8px;
                        font-weight: 500;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    ">
                        <i class="fas fa-redo"></i>
                        Начать сначала
                    </button>
                `;
                
                guessContainer.appendChild(actionsContainer);
                
                // Переподключаем обработчики событий
                const finalWatchBtn = document.getElementById('finalWatchBtn');
                const finalRestartBtn = document.getElementById('finalRestartBtn');
                
                if (finalWatchBtn) {
                    finalWatchBtn.addEventListener('click', handleWatchMovie);
                }
                if (finalRestartBtn) {
                    finalRestartBtn.addEventListener('click', restartOkkonator);
        }
        
        guessContainer.style.display = 'block';
            }
        } else {
            logError('Не удалось получить окончательные рекомендации');
            showErrorMessage('Не удалось получить рекомендации');
        }
    } catch (error) {
        logError('Ошибка при получении окончательных рекомендаций:', error);
        showErrorMessage('Ошибка получения рекомендаций');
    }
    
    isProcessing = false;
}

// Показать результаты на той же странице (при уверенности < 70%)
async function showResultsOnSamePage() {
    log('Показываем результаты на той же странице');
    
    try {
        // Получаем рекомендации от Окконатора
        const recommendations = await getOkkonatorRecommendations();
        
        if (recommendations.length > 0) {
            // Скрываем вопрос и варианты ответов
            const questionContainer = document.querySelector('.question-container');
            const answerOptions = document.querySelector('.answer-options');
            
            if (questionContainer) questionContainer.style.display = 'none';
            if (answerOptions) answerOptions.style.display = 'none';
            
            // Создаем контейнер для результатов
            const resultsContainer = document.createElement('div');
            resultsContainer.id = 'resultsContainer';
            resultsContainer.style.cssText = `
                background: var(--okko-surface);
                border-radius: var(--okko-radius-lg);
                padding: 24px;
                margin: 20px 0;
                border: 1px solid var(--okko-border);
            `;
            
            // Заголовок результатов
            const header = document.createElement('div');
            header.style.cssText = `
                text-align: center;
                margin-bottom: 24px;
            `;
            header.innerHTML = `
                <h3 style="color: var(--okko-text); font-size: 24px; font-weight: 600; margin: 0 0 8px 0;">
                    🎬 Ваши рекомендации готовы!
                </h3>
                <p style="color: var(--okko-text-muted); font-size: 16px; margin: 0;">
                    Мы подобрали фильмы на основе ваших предпочтений
                </p>
            `;
            resultsContainer.appendChild(header);
            
            // Сетка фильмов
            const moviesGrid = document.createElement('div');
            moviesGrid.style.cssText = `
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            `;
            
            // Показываем первые 6 фильмов
            recommendations.slice(0, 6).forEach((movie, index) => {
                const movieCard = document.createElement('div');
                movieCard.style.cssText = `
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease;
                    cursor: pointer;
                `;
                
                movieCard.innerHTML = `
                    <div style="
                        height: 200px;
                        background-image: url('${movie.poster || 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop'}');
                        background-size: cover;
                        background-position: center;
                        position: relative;
                    ">
                        <div style="
                            position: absolute;
                            top: 10px;
                            right: 10px;
                            background: rgba(0,0,0,0.7);
                            color: white;
                            padding: 4px 8px;
                            border-radius: 4px;
                            font-size: 12px;
                        ">${movie.rating || 'N/A'}</div>
                    </div>
                    <div style="padding: 15px;">
                        <h4 style="margin: 0 0 5px 0; font-size: 16px; color: #333;">${movie.title}</h4>
                        <p style="margin: 0 0 5px 0; font-size: 14px; color: #666;">${movie.year} • ${movie.duration || 'N/A'} мин</p>
                        <p style="margin: 0 0 10px 0; font-size: 12px; color: #888;">${movie.genre || 'Жанр не указан'}</p>
                        ${movie.reason ? `<p style="margin: 0; font-size: 11px; color: #999; font-style: italic;">${movie.reason}</p>` : ''}
                    </div>
                `;
                
                // Эффект при наведении
                movieCard.addEventListener('mouseenter', () => {
                    movieCard.style.transform = 'translateY(-5px)';
                });
                movieCard.addEventListener('mouseleave', () => {
                    movieCard.style.transform = 'translateY(0)';
                });
                
                moviesGrid.appendChild(movieCard);
            });
            
            resultsContainer.appendChild(moviesGrid);
            
            // Кнопки действий
            const actionsContainer = document.createElement('div');
            actionsContainer.style.cssText = `
                display: flex;
                gap: 15px;
                justify-content: center;
                margin-top: 20px;
                flex-wrap: wrap;
            `;
            
            actionsContainer.innerHTML = `
                <button class="action-btn primary-btn" id="viewResultsBtn" style="
                    background: var(--okko-primary);
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
                    Показать все результаты
                </button>
                <button class="action-btn secondary-btn" id="restartFromResultsBtn" style="
                    background: #f8f9fa;
                    color: #6c757d;
                    border: 1px solid #dee2e6;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 500;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                ">
                    <i class="fas fa-redo"></i>
                    Начать сначала
                </button>
            `;
            
            resultsContainer.appendChild(actionsContainer);
            
            // Добавляем контейнер на страницу
            const mainContent = document.querySelector('.okkonator-content');
            if (mainContent) {
                mainContent.appendChild(resultsContainer);
            }
            
            // Обработчики событий
            const viewResultsBtn = document.getElementById('viewResultsBtn');
            const restartFromResultsBtn = document.getElementById('restartFromResultsBtn');
            
            if (viewResultsBtn) {
                viewResultsBtn.addEventListener('click', () => {
                    // Сохраняем рекомендации и переходим на страницу результатов
                    localStorage.setItem('okkonator_recommendations', JSON.stringify(recommendations));
                    localStorage.setItem('okkonator_profile', JSON.stringify(userProfile));
                    window.location.href = '/results';
                });
            }
            
            if (restartFromResultsBtn) {
                restartFromResultsBtn.addEventListener('click', restartOkkonator);
            }
            
            logSuccess(`Показано ${recommendations.length} рекомендаций на той же странице`);
        } else {
            logError('Не удалось получить рекомендации');
            showErrorMessage('Не удалось получить рекомендации');
        }
    } catch (error) {
        logError('Ошибка при получении результатов:', error);
        showErrorMessage('Ошибка получения рекомендаций');
    }
}

// Обработка перехода к просмотру фильма
async function handleWatchMovie() {
    log('Нажата кнопка "Смотреть" для угаданного фильма');
    
    // Получаем информацию о фильме
    const guessTitle = document.getElementById('guessTitle');
    const guessYear = document.getElementById('guessYear');
    
    if (guessTitle && guessYear) {
        const movieTitle = guessTitle.textContent;
        const movieYear = guessYear.textContent;
        
        logSuccess(`Переходим к просмотру: ${movieTitle} (${movieYear})`);
        
        // Получаем полные рекомендации от Окконатора (используем кэш)
        const recommendations = await getOkkonatorRecommendations(true);
        if (recommendations.length > 0) {
            logSuccess(`Сохранено ${recommendations.length} рекомендаций для страницы результатов`);
            // Сохраняем рекомендации в localStorage для передачи на страницу результатов
            localStorage.setItem('okkonator_recommendations', JSON.stringify(recommendations));
            localStorage.setItem('okkonator_profile', JSON.stringify(userProfile));
        }
        
        // Показываем сообщение об успехе
        showSuccessMessage(`Переходим к просмотру "${movieTitle}" (${movieYear})`);
        
        // Переходим на страницу результатов
        setTimeout(() => {
            window.location.href = '/results';
        }, 2000);
    }
}

// Обработка ответа на угаданного кандидата
async function handleGuessResponse(isCorrect) {
    if (isCorrect) {
        log('Пользователь подтвердил угаданного кандидата');
        // Пользователь подтвердил угаданного кандидата
        showSuccessMessage();
        
        // Получаем полные рекомендации от Окконатора (используем кэш)
        const recommendations = await getOkkonatorRecommendations(true);
        if (recommendations.length > 0) {
            logSuccess(`Сохранено ${recommendations.length} рекомендаций для страницы результатов`);
            // Сохраняем рекомендации в localStorage для передачи на страницу результатов
            localStorage.setItem('okkonator_recommendations', JSON.stringify(recommendations));
            localStorage.setItem('okkonator_profile', JSON.stringify(userProfile));
        }
        
        setTimeout(() => {
            window.location.href = '/results';
        }, 2000);
    } else {
        log('Пользователь не подтвердил угаданного кандидата, продолжаем с вопросами');
        // Пользователь не подтвердил, продолжаем вопросы
        const guessContainer = document.getElementById('guessContainer');
        if (guessContainer) {
            guessContainer.style.display = 'none';
        }
        
        // Продолжаем с вопросами (только если уверенность < 100%)
        if (confidence < 100) {
            isProcessing = false;
        setTimeout(() => {
            loadNextQuestion();
            }, 1000);
        } else {
            log('Уверенность уже 100%, показываем окончательные рекомендации');
            showFinalRecommendations();
        }
    }
}

// Показать сообщение об успехе
function showSuccessMessage(message = 'Отлично! Мы угадали ваш фильм!') {
    const questionText = document.getElementById('questionText');
    if (questionText) {
        questionText.textContent = message;
        questionText.style.color = 'var(--okko-success)';
    }
}

// Обработка уточняющих чипов
function handleClarification(filter) {
    // Здесь можно добавить логику для уточняющих вопросов
    console.log('Уточнение:', filter);
    
    // Визуальная обратная связь
    const chip = document.querySelector(`[data-filter="${filter}"]`);
    if (chip) {
        chip.classList.add('active');
        setTimeout(() => {
            chip.classList.remove('active');
        }, 1000);
    }
}

// Показать опции завершения
function showCompletionOptions() {
    const questionText = document.getElementById('questionText');
    const continueBtn = document.getElementById('continueBtn');
    const showResultsBtn = document.getElementById('showResultsBtn');
    const goToChatBtn = document.getElementById('goToChatBtn');
    
    if (questionText) {
        questionText.textContent = 'Мы изучили ваши предпочтения! Что дальше?';
    }
    
    if (continueBtn) continueBtn.style.display = 'none';
    if (showResultsBtn) showResultsBtn.style.display = 'block';
    if (goToChatBtn) goToChatBtn.style.display = 'block';
    
    // Добавляем кнопку "Начать сначала"
    addRestartButton();
}

// Добавить кнопку "Начать сначала"
function addRestartButton() {
    // Проверяем, не добавлена ли уже кнопка
    if (document.getElementById('restartBtn')) return;
    
    const actionsContainer = document.querySelector('.okkonator-actions');
    if (actionsContainer) {
        const restartBtn = document.createElement('button');
        restartBtn.id = 'restartBtn';
        restartBtn.className = 'action-btn secondary-btn';
        restartBtn.innerHTML = `
            <i class="fas fa-redo"></i>
            Начать сначала
        `;
        restartBtn.style.cssText = `
            background: #f8f9fa;
            color: #6c757d;
            border: 1px solid #dee2e6;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
        `;
        
        restartBtn.addEventListener('click', restartOkkonator);
        actionsContainer.appendChild(restartBtn);
    }
}

// Перезапуск Окконатора
function restartOkkonator() {
    log('Перезапуск Окконатора - сброс всех параметров');
    
    // Очищаем localStorage
    clearStorage();
    
    // Сбрасываем все глобальные переменные
    currentQuestion = null;
    questionIndex = 0;
    confidence = 0;
    isProcessing = false;
    askedQuestions = [];
    userProfile = {};
    firstRecommendationsShown = false;
    
    // Скрываем угаданного кандидата
    const guessContainer = document.getElementById('guessContainer');
    if (guessContainer) {
        guessContainer.style.display = 'none';
    }
    
    // Сбрасываем индикатор уверенности и сохраняем в localStorage
    updateConfidence();
    saveToStorage(STORAGE_KEYS.CONFIDENCE, confidence);
    
    // Скрываем кнопки действий
    const continueBtn = document.getElementById('continueBtn');
    const showResultsBtn = document.getElementById('showResultsBtn');
    const goToChatBtn = document.getElementById('goToChatBtn');
    const restartBtn = document.getElementById('restartBtn');
    
    if (continueBtn) continueBtn.style.display = 'none';
    if (showResultsBtn) showResultsBtn.style.display = 'none';
    if (goToChatBtn) goToChatBtn.style.display = 'none';
    if (restartBtn) restartBtn.remove();
    
    // Показываем сообщение о перезапуске
    const questionText = document.getElementById('questionText');
    if (questionText) {
        questionText.textContent = 'Отлично! Начинаем заново. Ответьте на несколько вопросов, чтобы мы лучше поняли ваши предпочтения.';
        questionText.style.color = 'var(--okko-primary)';
    }
    
    logSuccess('Окконатор перезапущен');
    
    // Обновляем страницу для полного сброса состояния
    setTimeout(() => {
        window.location.reload();
    }, 1000);
}

// Показать сообщение об ошибке
function showErrorMessage(message) {
    const questionText = document.getElementById('questionText');
    if (questionText) {
        questionText.textContent = `Ошибка: ${message}`;
        questionText.style.color = 'var(--okko-error)';
    }
}

// Получить рекомендации от Окконатора
async function getOkkonatorRecommendations() {
    try {
        log('Запрашиваем рекомендации от Окконатора');
        showLoadingScreen('Получаем рекомендации...');
        
        const response = await fetch('/api/okkonator/recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                top_k: 6,
                theta: userProfile
            })
        });
        
        const data = await response.json();
        log('Получены рекомендации:', data);
        
        if (response.ok && data.recommendations) {
            logSuccess(`Получено ${data.recommendations.length} рекомендаций`);
            hideLoadingScreen();
            return data.recommendations;
        } else {
            logError('Ошибка получения рекомендаций:', data.error);
            showErrorMessage(data.error || 'Ошибка получения рекомендаций');
            hideLoadingScreen();
            return [];
        }
    } catch (error) {
        logError('Ошибка получения рекомендаций:', error);
        showErrorMessage('Ошибка подключения к сервису');
        hideLoadingScreen();
        return [];
    }
}

// Показать загрузочный экран
function showLoadingScreen(message, subtitle = null) {
    const loadingScreen = document.getElementById('loadingScreen');
    const loadingTitle = document.querySelector('.loading-title');
    const loadingText = document.querySelector('.loading-text');
    
    if (loadingScreen) {
        loadingScreen.style.display = 'flex';
    }
    if (loadingTitle && message) {
        loadingTitle.textContent = message;
    }
    if (loadingText && subtitle) {
        loadingText.textContent = subtitle;
    }
}

// Скрыть загрузочный экран
function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.style.display = 'none';
    }
}

// Анимация появления элементов
function animateOnScroll() {
    const elements = document.querySelectorAll('.answer-btn, .chip');
    
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
