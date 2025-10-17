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

/* ==============================
   Mood Measurement - Измерение настроения
   ============================== */

// Глобальные переменные для измерения настроения
let audioContext = null;
let analyser = null;
let microphone = null;
let dataArray = null;
let isRecording = false;
let recordingTimer = null;
let moodData = [];

// Инициализация измерения настроения
function initializeMoodMeasurement() {
    const moodBtn = document.getElementById('moodMeasurementBtn');
    const startMoodBtn = document.getElementById('startMoodBtn');
    const cancelMoodBtn = document.getElementById('cancelMoodBtn');
    
    if (moodBtn) {
        moodBtn.addEventListener('click', showMoodModal);
    }
    
    if (startMoodBtn) {
        startMoodBtn.addEventListener('click', startMoodMeasurement);
    }
    
    if (cancelMoodBtn) {
        cancelMoodBtn.addEventListener('click', hideMoodModal);
    }
}

// Показать модальное окно измерения настроения
function showMoodModal() {
    const modal = document.getElementById('moodModal');
    if (modal) {
        modal.classList.add('active');
        resetMoodMeasurement();
    }
}

// Скрыть модальное окно измерения настроения
function hideMoodModal() {
    const modal = document.getElementById('moodModal');
    if (modal) {
        modal.classList.remove('active');
        stopMoodMeasurement();
    }
}

// Сбросить состояние измерения настроения
function resetMoodMeasurement() {
    const volumeFill = document.getElementById('volumeFill');
    const timerText = document.getElementById('timerText');
    const timerFill = document.getElementById('timerFill');
    const moodStatus = document.getElementById('moodStatus');
    const startMoodBtn = document.getElementById('startMoodBtn');
    
    if (volumeFill) volumeFill.style.width = '0%';
    if (timerText) timerText.textContent = '5';
    if (timerFill) timerFill.style.background = 'conic-gradient(var(--okko-accent) 0deg, transparent 0deg)';
    if (moodStatus) {
        moodStatus.className = 'mood-status';
        moodStatus.innerHTML = '<i class="fas fa-microphone"></i><span>Готовы? Начинаем!</span>';
    }
    if (startMoodBtn) {
        startMoodBtn.style.display = 'flex';
        startMoodBtn.innerHTML = '<i class="fas fa-play"></i>Начать измерение';
    }
    
    moodData = [];
    isRecording = false;
}

// Начать измерение настроения
async function startMoodMeasurement() {
    try {
        // Запрос доступа к микрофону
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Инициализация Web Audio API
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);
        
        analyser.fftSize = 256;
        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);
        
        microphone.connect(analyser);
        
        // Обновление UI
        updateMoodStatus('recording', 'Кричите громче!');
        const startMoodBtn = document.getElementById('startMoodBtn');
        if (startMoodBtn) {
            startMoodBtn.style.display = 'none';
        }
        
        // Запуск измерения
        isRecording = true;
        startMoodTimer();
        startVolumeMonitoring();
        
    } catch (error) {
        console.error('Ошибка доступа к микрофону:', error);
        updateMoodStatus('error', 'Не удалось получить доступ к микрофону');
    }
}

// Запуск таймера измерения
function startMoodTimer() {
    let timeLeft = 5;
    const timerText = document.getElementById('timerText');
    const timerFill = document.getElementById('timerFill');
    
    recordingTimer = setInterval(() => {
        timeLeft--;
        
        if (timerText) {
            timerText.textContent = timeLeft;
        }
        
        if (timerFill) {
            const progress = ((5 - timeLeft) / 5) * 360;
            timerFill.style.background = `conic-gradient(var(--okko-accent) ${progress}deg, transparent ${progress}deg)`;
        }
        
        if (timeLeft <= 0) {
            stopMoodMeasurement();
            analyzeMood();
        }
    }, 1000);
}

// Мониторинг громкости
function startVolumeMonitoring() {
    if (!isRecording) return;
    
    analyser.getByteFrequencyData(dataArray);
    
    // Вычисление средней громкости
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
    }
    const average = sum / dataArray.length;
    const volumePercent = Math.min((average / 128) * 100, 100);
    
    // Сохранение данных
    moodData.push({
        timestamp: Date.now(),
        volume: volumePercent,
        rawData: Array.from(dataArray)
    });
    
    // Обновление визуального индикатора
    updateVolumeIndicator(volumePercent);
    
    // Продолжение мониторинга
    if (isRecording) {
        requestAnimationFrame(startVolumeMonitoring);
    }
}

// Обновление индикатора громкости
function updateVolumeIndicator(volumePercent) {
    const volumeFill = document.getElementById('volumeFill');
    if (volumeFill) {
        volumeFill.style.width = `${volumePercent}%`;
    }
}

// Обновление статуса
function updateMoodStatus(status, message) {
    const moodStatus = document.getElementById('moodStatus');
    if (moodStatus) {
        moodStatus.className = `mood-status ${status}`;
        
        let icon = 'fas fa-microphone';
        if (status === 'recording') icon = 'fas fa-microphone';
        else if (status === 'analyzing') icon = 'fas fa-cog';
        else if (status === 'error') icon = 'fas fa-exclamation-triangle';
        else if (status === 'success') icon = 'fas fa-check-circle';
        
        moodStatus.innerHTML = `<i class="${icon}"></i><span>${message}</span>`;
    }
}

// Остановка измерения
function stopMoodMeasurement() {
    isRecording = false;
    
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }
    
    if (microphone) {
        microphone.disconnect();
    }
    
    if (audioContext) {
        audioContext.close();
    }
    
    // Остановка потока микрофона
    if (microphone && microphone.mediaStream) {
        microphone.mediaStream.getTracks().forEach(track => track.stop());
    }
}

// Анализ настроения
function analyzeMood() {
    updateMoodStatus('analyzing', 'Анализируем настроение...');
    
    setTimeout(() => {
        const moodResult = calculateMood(moodData);
        displayMoodResult(moodResult);
    }, 2000);
}

// Вычисление настроения на основе данных
function calculateMood(data) {
    if (!data || data.length === 0) {
        return {
            mood: 'неопределенное',
            energy: 0,
            confidence: 0,
            description: 'Не удалось определить настроение'
        };
    }
    
    // Вычисление средней громкости
    const avgVolume = data.reduce((sum, point) => sum + point.volume, 0) / data.length;
    
    // Вычисление максимальной громкости
    const maxVolume = Math.max(...data.map(point => point.volume));
    
    // Вычисление вариативности (насколько сильно менялась громкость)
    const variance = data.reduce((sum, point) => sum + Math.pow(point.volume - avgVolume, 2), 0) / data.length;
    
    // Определение настроения
    let mood, energy, confidence, description;
    
    if (avgVolume < 20) {
        mood = 'спокойное';
        energy = 20;
        confidence = 85;
        description = 'Группа настроена спокойно и расслабленно';
    } else if (avgVolume < 50) {
        mood = 'умеренное';
        energy = 50;
        confidence = 75;
        description = 'Группа в хорошем настроении, готова к просмотру';
    } else if (avgVolume < 80) {
        mood = 'энергичное';
        energy = 80;
        confidence = 90;
        description = 'Группа полна энергии и энтузиазма!';
    } else {
        mood = 'очень энергичное';
        energy = 95;
        confidence = 95;
        description = 'Группа в отличном настроении и готова к активному просмотру!';
    }
    
    // Корректировка на основе вариативности
    if (variance > 500) {
        confidence -= 10;
        description += ' (замечена высокая вариативность в настроении)';
    }
    
    return {
        mood,
        energy: Math.round(energy),
        confidence: Math.round(confidence),
        description,
        avgVolume: Math.round(avgVolume),
        maxVolume: Math.round(maxVolume),
        variance: Math.round(variance)
    };
}

// Отображение результата
function displayMoodResult(result) {
    updateMoodStatus('success', `Настроение: ${result.mood}`);
    
    // Создание результата
    const resultHtml = `
        <div class="mood-result">
            <h3>Результат измерения настроения</h3>
            <div class="mood-stats">
                <div class="mood-stat">
                    <span class="stat-label">Настроение:</span>
                    <span class="stat-value">${result.mood}</span>
                </div>
                <div class="mood-stat">
                    <span class="stat-label">Энергия:</span>
                    <span class="stat-value">${result.energy}%</span>
                </div>
                <div class="mood-stat">
                    <span class="stat-label">Уверенность:</span>
                    <span class="stat-value">${result.confidence}%</span>
                </div>
            </div>
            <p class="mood-description">${result.description}</p>
        </div>
        <div class="mood-controls">
            <button class="action-btn secondary-btn" id="closeMoodBtn" style="width: 100%;">
                <i class="fas fa-times"></i>
                Закрыть
            </button>
        </div>
    `;
    
    // Замена содержимого модального окна
    const moodMeasurement = document.querySelector('.mood-measurement');
    if (moodMeasurement) {
        moodMeasurement.innerHTML = resultHtml;
    }
    
    // Показ кнопки закрытия
    const moodControls = document.querySelector('.mood-controls');
    if (moodControls) {
        moodControls.style.display = 'flex';
        moodControls.innerHTML = `
            <button class="action-btn secondary-btn" id="closeMoodBtn" style="flex: 1; max-width: 200px;">
                <i class="fas fa-times"></i>
                Закрыть
            </button>
        `;
        
        const closeBtn = document.getElementById('closeMoodBtn');
        if (closeBtn) {
            closeBtn.addEventListener('click', hideMoodModal);
        }
    } else {
        // Если контейнер не найден, создаем его
        const moodMeasurement = document.querySelector('.mood-measurement');
        if (moodMeasurement) {
            const controlsDiv = document.createElement('div');
            controlsDiv.className = 'mood-controls';
            controlsDiv.innerHTML = `
                <button class="action-btn secondary-btn" id="closeMoodBtn" style="flex: 1; max-width: 200px;">
                    <i class="fas fa-times"></i>
                    Закрыть
                </button>
            `;
            moodMeasurement.appendChild(controlsDiv);
            
            const closeBtn = document.getElementById('closeMoodBtn');
            if (closeBtn) {
                closeBtn.addEventListener('click', hideMoodModal);
            }
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeMoodMeasurement();
});
