/* ==============================
   Okkonator - Экран вопросов и ответов
   ============================== */

// Глобальные переменные
let currentQuestion = null;
let questionIndex = 0;
let confidence = 0;
let isProcessing = false;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeOkkonator();
});

// Основная инициализация
function initializeOkkonator() {
    hideLoadingScreen();
    setupEventListeners();
    loadNextQuestion();
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
    const correctBtn = document.getElementById('correctBtn');
    const wrongBtn = document.getElementById('wrongBtn');
    
    if (correctBtn) {
        correctBtn.addEventListener('click', () => {
            handleGuessResponse(true);
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
        showResultsBtn.addEventListener('click', () => {
            window.location.href = '/results';
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
    if (isProcessing) return;
    
    try {
        showLoadingScreen('Загружаем вопрос...');
        
        const response = await fetch('/api/okkonator/question');
        const data = await response.json();
        
        if (data.question) {
            currentQuestion = data;
            questionIndex = data.question_id;
            confidence = data.confidence;
            
            displayQuestion();
            updateConfidence();
            hideLoadingScreen();
        } else {
            // Вопросы закончились
            showCompletionOptions();
        }
    } catch (error) {
        console.error('Ошибка загрузки вопроса:', error);
        hideLoadingScreen();
    }
}

// Отображение вопроса
function displayQuestion() {
    const questionText = document.getElementById('questionText');
    if (questionText && currentQuestion) {
        questionText.textContent = currentQuestion.question;
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
    if (isProcessing) return;
    
    isProcessing = true;
    
    try {
        // Отправляем ответ на сервер
        const response = await fetch('/api/okkonator/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                answer: answer,
                question_id: questionIndex
            })
        });
        
        if (response.ok) {
            // Обновляем уверенность
            confidence = Math.min(confidence + 10, 100);
            updateConfidence();
            
            // Проверяем, нужно ли показать угаданного кандидата
            if (confidence >= 70) {
                showGuessedCandidate();
            } else {
                // Продолжаем с вопросами
                setTimeout(() => {
                    loadNextQuestion();
                    isProcessing = false;
                }, 1000);
            }
        }
    } catch (error) {
        console.error('Ошибка отправки ответа:', error);
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
function showGuessedCandidate() {
    const guessContainer = document.getElementById('guessContainer');
    const guessPoster = document.getElementById('guessPoster');
    const guessTitle = document.getElementById('guessTitle');
    const guessYear = document.getElementById('guessYear');
    const guessConfidence = document.getElementById('guessConfidence');
    
    if (guessContainer) {
        // Моковые данные для демонстрации
        const mockCandidate = {
            title: 'Blade Runner 2049',
            year: 2017,
            poster: 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop',
            confidence: confidence
        };
        
        if (guessPoster) {
            guessPoster.style.backgroundImage = `url('${mockCandidate.poster}')`;
        }
        if (guessTitle) {
            guessTitle.textContent = mockCandidate.title;
        }
        if (guessYear) {
            guessYear.textContent = mockCandidate.year;
        }
        if (guessConfidence) {
            guessConfidence.textContent = mockCandidate.confidence;
        }
        
        guessContainer.style.display = 'block';
    }
    
    isProcessing = false;
}

// Обработка ответа на угаданного кандидата
function handleGuessResponse(isCorrect) {
    if (isCorrect) {
        // Пользователь подтвердил угаданного кандидата
        showSuccessMessage();
        setTimeout(() => {
            window.location.href = '/results';
        }, 2000);
    } else {
        // Пользователь не подтвердил, продолжаем вопросы
        const guessContainer = document.getElementById('guessContainer');
        if (guessContainer) {
            guessContainer.style.display = 'none';
        }
        
        // Снижаем уверенность и продолжаем
        confidence = Math.max(confidence - 20, 0);
        updateConfidence();
        
        setTimeout(() => {
            loadNextQuestion();
        }, 500);
    }
}

// Показать сообщение об успехе
function showSuccessMessage() {
    const questionText = document.getElementById('questionText');
    if (questionText) {
        questionText.textContent = 'Отлично! Мы угадали ваш фильм!';
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
}

// Показать загрузочный экран
function showLoadingScreen(message) {
    const loadingScreen = document.getElementById('loadingScreen');
    const loadingTitle = document.querySelector('.loading-title');
    
    if (loadingScreen) {
        loadingScreen.style.display = 'flex';
    }
    if (loadingTitle && message) {
        loadingTitle.textContent = message;
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
