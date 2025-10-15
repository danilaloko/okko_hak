/* ==============================
   Demo - Демо-режим с пошаговым сценарием
   ============================== */

// Глобальные переменные
let currentStep = 1;
let totalSteps = 5;
let isDemoRunning = false;
let demoTimeout = null;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeDemo();
});

// Основная инициализация
function initializeDemo() {
    hideLoadingScreen();
    setupEventListeners();
    updateProgress();
    startDemo();
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
    
    // Кнопка выхода из демо
    const exitDemoBtn = document.getElementById('exitDemoBtn');
    if (exitDemoBtn) {
        exitDemoBtn.addEventListener('click', () => {
            exitDemo();
        });
    }
    
    // Кнопки управления демо
    const prevStepBtn = document.getElementById('prevStepBtn');
    const nextStepBtn = document.getElementById('nextStepBtn');
    const skipStepBtn = document.getElementById('skipStepBtn');
    
    if (prevStepBtn) {
        prevStepBtn.addEventListener('click', () => {
            goToPreviousStep();
        });
    }
    if (nextStepBtn) {
        nextStepBtn.addEventListener('click', () => {
            goToNextStep();
        });
    }
    if (skipStepBtn) {
        skipStepBtn.addEventListener('click', () => {
            skipCurrentStep();
        });
    }
    
    // Интерактивные элементы демо
    setupDemoInteractions();
}

// Настройка интерактивных элементов демо
function setupDemoInteractions() {
    // Демо карточки в блоке 1 (Свайпы)
    const demoCards = document.querySelectorAll('.demo-card');
    demoCards.forEach(card => {
        card.addEventListener('click', () => {
            if (currentStep === 1) {
                simulateSwipe();
            }
        });
    });
    
    // Демо кнопки в блоке 1
    const demoBtns = document.querySelectorAll('.demo-btn');
    demoBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentStep === 1) {
                const action = btn.classList.contains('dislike-btn') ? 'dislike' : 'like';
                simulateSwipeAction(action);
            }
        });
    });
    
    // Демо ответы в блоке 2 (Окконатор)
    const demoAnswerBtns = document.querySelectorAll('.demo-answer-btn');
    demoAnswerBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentStep === 2) {
                simulateAnswer();
            }
        });
    });
    
    // Демо анализ в блоке 3 (Узнать фильм)
    const demoAnalyzeBtn = document.querySelector('.demo-analyze-btn');
    if (demoAnalyzeBtn) {
        demoAnalyzeBtn.addEventListener('click', () => {
            if (currentStep === 3) {
                simulateAnalysis();
            }
        });
    }
    
    // Демо чат в блоке 4
    const demoSendBtn = document.querySelector('.demo-send-btn');
    if (demoSendBtn) {
        demoSendBtn.addEventListener('click', () => {
            if (currentStep === 4) {
                simulateChatMessage();
            }
        });
    }
    
    // Демо действия в блоке 5
    const demoActionBtns = document.querySelectorAll('.demo-action-btn');
    demoActionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentStep === 5) {
                simulateFinalAction();
            }
        });
    });
}

// Запуск демо
function startDemo() {
    isDemoRunning = true;
    showStep(1);
    
    // Автоматический переход к следующему шагу через 30 секунд
    demoTimeout = setTimeout(() => {
        if (currentStep < totalSteps) {
            goToNextStep();
        }
    }, 30000);
}

// Показать шаг
function showStep(step) {
    currentStep = step;
    
    // Скрываем все шаги
    const steps = document.querySelectorAll('.demo-step');
    steps.forEach(stepEl => {
        stepEl.classList.remove('active');
    });
    
    // Показываем текущий шаг
    const currentStepEl = document.getElementById(`step${step}`);
    if (currentStepEl) {
        currentStepEl.classList.add('active');
    }
    
    // Обновляем прогресс
    updateProgress();
    updateStepButtons();
    
    // Запускаем анимации для текущего шага
    animateCurrentStep();
}

// Обновление прогресса
function updateProgress() {
    const progressFill = document.getElementById('demoProgressFill');
    const progress = (currentStep / totalSteps) * 100;
    
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
    }
    
    // Обновляем активные шаги
    const stepElements = document.querySelectorAll('.step');
    stepElements.forEach((stepEl, index) => {
        const stepNumber = index + 1;
        if (stepNumber <= currentStep) {
            stepEl.classList.add('active');
        } else {
            stepEl.classList.remove('active');
        }
    });
}

// Обновление кнопок управления
function updateStepButtons() {
    const prevStepBtn = document.getElementById('prevStepBtn');
    const nextStepBtn = document.getElementById('nextStepBtn');
    
    if (prevStepBtn) {
        prevStepBtn.disabled = currentStep === 1;
    }
    if (nextStepBtn) {
        nextStepBtn.disabled = currentStep === totalSteps;
    }
}

// Переход к следующему шагу
function goToNextStep() {
    if (currentStep < totalSteps) {
        showLoadingScreen('Переходим к следующему блоку...', 'Подготавливаем демонстрацию');
        
        setTimeout(() => {
            hideLoadingScreen();
            showStep(currentStep + 1);
            
            // Устанавливаем таймер для следующего шага
            if (currentStep < totalSteps) {
                demoTimeout = setTimeout(() => {
                    goToNextStep();
                }, getStepDuration(currentStep));
            } else {
                showMetrics();
            }
        }, 1000);
    }
}

// Переход к предыдущему шагу
function goToPreviousStep() {
    if (currentStep > 1) {
        showStep(currentStep - 1);
        
        // Очищаем таймер
        if (demoTimeout) {
            clearTimeout(demoTimeout);
        }
        
        // Устанавливаем новый таймер
        demoTimeout = setTimeout(() => {
            goToNextStep();
        }, getStepDuration(currentStep - 1));
    }
}

// Пропуск текущего шага
function skipCurrentStep() {
    goToNextStep();
}

// Получение длительности шага
function getStepDuration(step) {
    const durations = {
        1: 30000, // 30 секунд для свайпов
        2: 40000, // 40 секунд для окконатора
        3: 30000, // 30 секунд для узнавания фильма
        4: 40000, // 40 секунд для чата
        5: 20000  // 20 секунд для результатов
    };
    return durations[step] || 30000;
}

// Анимация текущего шага
function animateCurrentStep() {
    const currentStepEl = document.getElementById(`step${currentStep}`);
    if (!currentStepEl) return;
    
    // Анимация появления элементов
    const elements = currentStepEl.querySelectorAll('.demo-card, .demo-btn, .demo-answer-btn');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
            element.style.transition = 'all 0.6s ease';
        }, index * 200);
    });
}

// Симуляция свайпа
function simulateSwipe() {
    const demoCard = document.getElementById('demoCard1');
    if (demoCard) {
        demoCard.style.transform = 'translateX(100px) rotate(15deg)';
        demoCard.style.opacity = '0.7';
        
        setTimeout(() => {
            demoCard.style.transform = '';
            demoCard.style.opacity = '';
        }, 1000);
    }
}

// Симуляция действия свайпа
function simulateSwipeAction(action) {
    const demoCard = document.getElementById('demoCard1');
    if (demoCard) {
        if (action === 'like') {
            demoCard.style.transform = 'translateX(100vw) rotate(30deg)';
        } else {
            demoCard.style.transform = 'translateX(-100vw) rotate(-30deg)';
        }
        demoCard.style.opacity = '0';
        
        setTimeout(() => {
            demoCard.style.transform = '';
            demoCard.style.opacity = '';
        }, 1000);
    }
}

// Симуляция ответа в окконаторе
function simulateAnswer() {
    const confidenceBar = document.querySelector('.confidence-fill');
    if (confidenceBar) {
        const currentWidth = parseInt(confidenceBar.style.width) || 30;
        const newWidth = Math.min(currentWidth + 20, 100);
        confidenceBar.style.width = `${newWidth}%`;
        
        const confidenceText = document.querySelector('.confidence-text');
        if (confidenceText) {
            confidenceText.textContent = `Уверенность: ${newWidth}%`;
        }
    }
}

// Симуляция анализа
function simulateAnalysis() {
    const demoCandidates = document.querySelector('.demo-candidates');
    if (demoCandidates) {
        demoCandidates.style.display = 'block';
        
        // Анимация появления кандидатов
        const candidates = demoCandidates.querySelectorAll('.candidate-card');
        candidates.forEach((candidate, index) => {
            candidate.style.opacity = '0';
            candidate.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                candidate.style.opacity = '1';
                candidate.style.transform = 'translateY(0)';
                candidate.style.transition = 'all 0.6s ease';
            }, index * 300);
        });
    }
}

// Симуляция сообщения в чате
function simulateChatMessage() {
    const demoMessages = document.querySelector('.demo-messages');
    if (demoMessages) {
        const newMessage = document.createElement('div');
        newMessage.className = 'demo-message user';
        newMessage.innerHTML = `
            <div class="message-text">Хочу что-то короткое и лёгкое</div>
        `;
        
        demoMessages.appendChild(newMessage);
        
        // Анимация появления
        newMessage.style.opacity = '0';
        newMessage.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            newMessage.style.opacity = '1';
            newMessage.style.transform = 'translateY(0)';
            newMessage.style.transition = 'all 0.6s ease';
        }, 100);
    }
}

// Симуляция финального действия
function simulateFinalAction() {
    const demoRecommendations = document.querySelector('.demo-recommendations');
    if (demoRecommendations) {
        // Анимация появления рекомендаций
        const recommendations = demoRecommendations.querySelectorAll('.demo-recommendation-card');
        recommendations.forEach((rec, index) => {
            rec.style.opacity = '0';
            rec.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                rec.style.opacity = '1';
                rec.style.transform = 'translateY(0)';
                rec.style.transition = 'all 0.6s ease';
            }, index * 200);
        });
    }
}

// Показать метрики
function showMetrics() {
    const metricsSection = document.getElementById('demoMetrics');
    if (metricsSection) {
        metricsSection.style.display = 'block';
        
        // Анимация появления метрик
        const metricCards = metricsSection.querySelectorAll('.metric-card');
        metricCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                card.style.transition = 'all 0.6s ease';
            }, index * 200);
        });
    }
}

// Выход из демо
function exitDemo() {
    if (demoTimeout) {
        clearTimeout(demoTimeout);
    }
    isDemoRunning = false;
    window.location.href = '/';
}

// Показать загрузочный экран
function showLoadingScreen(title, text) {
    const loadingScreen = document.getElementById('loadingScreen');
    const loadingTitle = document.getElementById('loadingTitle');
    const loadingText = document.getElementById('loadingText');
    
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

// Очистка при выходе
window.addEventListener('beforeunload', () => {
    if (demoTimeout) {
        clearTimeout(demoTimeout);
    }
});
