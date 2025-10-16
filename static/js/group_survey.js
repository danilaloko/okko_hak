/* ==============================
   Group Survey - Групповой опрос
   ============================== */

// Глобальные переменные
let participantsCount = 0;
let currentParticipant = 1;
let currentQuestion = 0;
let participantAnswers = {};
let groupAnswers = {};
let isProcessing = false;

// Вопросы для опроса (одинаковые для всех участников)
const surveyQuestions = [
    "Предпочитаете современные фильмы (после 2010)?",
    "Нравится фантастика?",
    "Любите драматические сюжеты?",
    "Интересуют боевики?"
];

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeGroupSurvey();
});

// Основная инициализация
function initializeGroupSurvey() {
    hideLoadingScreen();
    setupEventListeners();
    showParticipantsStep();
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
    
    // Кнопки выбора количества участников
    const participantBtns = document.querySelectorAll('.participant-btn');
    participantBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const count = parseInt(btn.dataset.count);
            selectParticipantsCount(count);
        });
    });
    
    // Кнопки ответов
    const answerBtns = document.querySelectorAll('.answer-btn');
    answerBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const answer = btn.dataset.answer;
            handleAnswer(answer);
        });
    });
    
    // Кнопка начала опроса участника
    const startParticipantBtn = document.getElementById('startParticipantBtn');
    if (startParticipantBtn) {
        startParticipantBtn.addEventListener('click', () => {
            hideParticipantModal();
            startParticipantSurvey();
        });
    }
    
    // Кнопки результатов
    const startWatchingBtn = document.getElementById('startWatchingBtn');
    const newSurveyBtn = document.getElementById('newSurveyBtn');
    
    if (startWatchingBtn) {
        startWatchingBtn.addEventListener('click', () => {
            window.location.href = '/results';
        });
    }
    if (newSurveyBtn) {
        newSurveyBtn.addEventListener('click', () => {
            resetSurvey();
        });
    }
}

// Показать этап выбора участников
function showParticipantsStep() {
    const participantsStep = document.getElementById('participantsStep');
    const surveyStep = document.getElementById('surveyStep');
    const resultsStep = document.getElementById('resultsStep');
    
    if (participantsStep) participantsStep.style.display = 'block';
    if (surveyStep) surveyStep.style.display = 'none';
    if (resultsStep) resultsStep.style.display = 'none';
}

// Выбор количества участников
function selectParticipantsCount(count) {
    participantsCount = count;
    currentParticipant = 1;
    currentQuestion = 0;
    participantAnswers = {};
    groupAnswers = {};
    
    // Анимация выбора
    const selectedBtn = document.querySelector(`[data-count="${count}"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('selected');
        setTimeout(() => {
            startSurvey();
        }, 500);
    }
}

// Начать опрос
function startSurvey() {
    const participantsStep = document.getElementById('participantsStep');
    
    if (participantsStep) participantsStep.style.display = 'none';
    
    // Показываем модальное окно для первого участника
    showParticipantModal();
}

// Показать модальное окно участника
function showParticipantModal() {
    const modal = document.getElementById('participantModal');
    const callTitle = document.getElementById('participantCallTitle');
    
    if (modal) {
        // Обновляем заголовок в зависимости от номера участника
        const titles = [
            "Первому игроку приготовиться!",
            "Второму игроку приготовиться!",
            "Третьему игроку приготовиться!",
            "Четвертому игроку приготовиться!",
            "Пятому игроку приготовиться!"
        ];
        
        if (callTitle) {
            callTitle.textContent = titles[currentParticipant - 1] || "Участнику приготовиться!";
        }
        
        modal.classList.add('active');
    }
}

// Скрыть модальное окно участника
function hideParticipantModal() {
    const modal = document.getElementById('participantModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Начать опрос текущего участника
function startParticipantSurvey() {
    const surveyStep = document.getElementById('surveyStep');
    
    if (surveyStep) surveyStep.style.display = 'block';
    
    updateParticipantProgress();
    loadCurrentQuestion();
}

// Обновить прогресс участника
function updateParticipantProgress() {
    const currentParticipantEl = document.querySelector('.current-participant');
    const progressCounter = document.querySelector('.progress-counter');
    const participantProgress = document.getElementById('participantProgress');
    
    if (currentParticipantEl) {
        currentParticipantEl.textContent = `Участник ${currentParticipant}`;
    }
    if (progressCounter) {
        progressCounter.textContent = `${currentParticipant} из ${participantsCount}`;
    }
    if (participantProgress) {
        const progress = (currentParticipant - 1) / participantsCount * 100;
        participantProgress.style.width = `${progress}%`;
    }
}

// Загрузить текущий вопрос
function loadCurrentQuestion() {
    if (currentQuestion < surveyQuestions.length) {
        const questionText = document.getElementById('questionText');
        if (questionText) {
            questionText.textContent = surveyQuestions[currentQuestion];
        }
    } else {
        // Вопросы для текущего участника закончились
        finishCurrentParticipant();
    }
}

// Обработка ответа
function handleAnswer(answer) {
    if (isProcessing) return;
    
    isProcessing = true;
    
    // Сохраняем ответ текущего участника
    if (!participantAnswers[currentParticipant]) {
        participantAnswers[currentParticipant] = {};
    }
    participantAnswers[currentParticipant][currentQuestion] = answer;
    
    // Визуальная обратная связь
    const answerBtns = document.querySelectorAll('.answer-btn');
    answerBtns.forEach(btn => {
        btn.classList.remove('selected');
        if (btn.dataset.answer === answer) {
            btn.classList.add('selected');
        }
    });
    
    setTimeout(() => {
        currentQuestion++;
        if (currentQuestion < surveyQuestions.length) {
            loadCurrentQuestion();
        } else {
            finishCurrentParticipant();
        }
        isProcessing = false;
    }, 500);
}

// Завершить опрос текущего участника
function finishCurrentParticipant() {
    currentQuestion = 0;
    currentParticipant++;
    
    if (currentParticipant <= participantsCount) {
        // Скрываем опрос и показываем модальное окно для следующего участника
        const surveyStep = document.getElementById('surveyStep');
        if (surveyStep) surveyStep.style.display = 'none';
        
        // Показываем модальное окно для следующего участника
        showParticipantModal();
    } else {
        // Все участники прошли опрос
        finishSurvey();
    }
}

// Завершить опрос
function finishSurvey() {
    showLoadingScreen('Анализируем ответы всех участников...');
    
    setTimeout(() => {
        hideLoadingScreen();
        showResults();
    }, 2000);
}

// Показать результаты
function showResults() {
    const surveyStep = document.getElementById('surveyStep');
    const resultsStep = document.getElementById('resultsStep');
    
    if (surveyStep) surveyStep.style.display = 'none';
    if (resultsStep) resultsStep.style.display = 'block';
    
    loadGroupRecommendations();
}

// Загрузить рекомендации для группы
function loadGroupRecommendations() {
    const recommendationsContainer = document.getElementById('groupRecommendations');
    
    if (recommendationsContainer) {
        // Моковые данные для демонстрации
        const mockRecommendations = [
            {
                title: "Интерстеллар",
                year: 2014,
                genre: "Фантастика, Драма",
                rating: 8.6,
                poster: "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=400&h=600&fit=crop",
                reason: "Подходит всем участникам группы",
                matchScore: 95
            },
            {
                title: "Дюна",
                year: 2021,
                genre: "Фантастика, Приключения",
                rating: 8.0,
                poster: "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop",
                reason: "Эпическая фантастика для всей группы",
                matchScore: 88
            },
            {
                title: "Темный рыцарь",
                year: 2008,
                genre: "Боевик, Криминал",
                rating: 9.0,
                poster: "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop",
                reason: "Классика, которая понравится всем",
                matchScore: 82
            }
        ];
        
        recommendationsContainer.innerHTML = '';
        
        mockRecommendations.forEach((movie, index) => {
            const movieCard = createMovieCard(movie, index);
            recommendationsContainer.appendChild(movieCard);
        });
    }
}

// Создать карточку фильма
function createMovieCard(movie, index) {
    const card = document.createElement('div');
    card.className = 'recommendation-card';
    card.innerHTML = `
        <div class="recommendation-poster" style="background-image: url('${movie.poster}')"></div>
        <div class="recommendation-info">
            <div class="recommendation-title">${movie.title}</div>
            <div class="recommendation-meta">
                <span class="recommendation-year">${movie.year}</span>
                <span class="recommendation-genre">${movie.genre}</span>
                <span class="recommendation-rating">${movie.rating}</span>
            </div>
            <div class="recommendation-reason">${movie.reason}</div>
            <div class="match-score">
                Совпадение: <span class="score-value">${movie.matchScore}%</span>
            </div>
        </div>
    `;
    
    return card;
}

// Сбросить опрос
function resetSurvey() {
    participantsCount = 0;
    currentParticipant = 1;
    currentQuestion = 0;
    participantAnswers = {};
    groupAnswers = {};
    
    // Скрыть модальное окно
    hideParticipantModal();
    
    // Сбросить визуальные состояния
    const selectedBtns = document.querySelectorAll('.participant-btn.selected');
    selectedBtns.forEach(btn => btn.classList.remove('selected'));
    
    const selectedAnswers = document.querySelectorAll('.answer-btn.selected');
    selectedAnswers.forEach(btn => btn.classList.remove('selected'));
    
    showParticipantsStep();
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
    const elements = document.querySelectorAll('.participant-btn, .answer-btn, .recommendation-card');
    
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
