/* ==============================
   Identify - Экран идентификации фильмов
   ============================== */

// Глобальные переменные
let currentTab = 'link';
let isAnalyzing = false;
let currentCandidates = [];

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeIdentify();
});

// Основная инициализация
function initializeIdentify() {
    hideLoadingScreen();
    setupEventListeners();
    setupDragAndDrop();
    setupVoiceRecording();
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
    
    // Переключатели вкладок
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
    
    // Анализ по URL
    const analyzeUrlBtn = document.getElementById('analyzeUrlBtn');
    if (analyzeUrlBtn) {
        analyzeUrlBtn.addEventListener('click', analyzeUrl);
    }
    
    // Анализ по описанию
    const analyzeDescriptionBtn = document.getElementById('analyzeDescriptionBtn');
    if (analyzeDescriptionBtn) {
        analyzeDescriptionBtn.addEventListener('click', analyzeDescription);
    }
    
    // Выбор файла
    const fileSelectBtn = document.getElementById('fileSelectBtn');
    const fileInput = document.getElementById('fileInput');
    
    if (fileSelectBtn && fileInput) {
        fileSelectBtn.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFileSelect(e.target.files[0]);
        });
    }
    
    // Голосовая запись
    const voiceRecordBtn = document.getElementById('voiceRecordBtn');
    if (voiceRecordBtn) {
        voiceRecordBtn.addEventListener('click', toggleVoiceRecording);
    }
    
    // Кнопки результатов
    const refineSearchBtn = document.getElementById('refineSearchBtn');
    const showSimilarBtn = document.getElementById('showSimilarBtn');
    
    if (refineSearchBtn) {
        refineSearchBtn.addEventListener('click', () => {
            showClarificationQuestions();
        });
    }
    if (showSimilarBtn) {
        showSimilarBtn.addEventListener('click', () => {
            window.location.href = '/results';
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

// Переключение вкладок
function switchTab(tab) {
    currentTab = tab;
    
    // Обновляем активную вкладку
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        }
    });
    
    // Показываем соответствующее содержимое
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
        if (content.id === `${tab}Tab`) {
            content.classList.add('active');
        }
    });
}

// Анализ URL
async function analyzeUrl() {
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();
    
    if (!url) {
        alert('Пожалуйста, введите URL');
        return;
    }
    
    if (isAnalyzing) return;
    
    try {
        showLoadingScreen('Анализируем видео...', 'Это может занять несколько секунд');
        
        const response = await fetch('/api/identify/url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        if (response.ok) {
            const data = await response.json();
            currentCandidates = data.candidates;
            showResults(data.candidates);
        } else {
            throw new Error('Ошибка анализа URL');
        }
    } catch (error) {
        console.error('Ошибка анализа URL:', error);
        alert('Ошибка при анализе URL. Попробуйте еще раз.');
    } finally {
        hideLoadingScreen();
    }
}

// Анализ описания
async function analyzeDescription() {
    const descriptionInput = document.getElementById('descriptionInput');
    const description = descriptionInput.value.trim();
    
    if (!description) {
        alert('Пожалуйста, введите описание фильма');
        return;
    }
    
    if (isAnalyzing) return;
    
    try {
        showLoadingScreen('Анализируем описание...', 'Ищем подходящие фильмы');
        
        const response = await fetch('/api/identify/description', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ description: description })
        });
        
        if (response.ok) {
            const data = await response.json();
            currentCandidates = data.candidates;
            showResults(data.candidates);
        } else {
            throw new Error('Ошибка анализа описания');
        }
    } catch (error) {
        console.error('Ошибка анализа описания:', error);
        alert('Ошибка при анализе описания. Попробуйте еще раз.');
    } finally {
        hideLoadingScreen();
    }
}

// Показать результаты
function showResults(candidates) {
    const resultsSection = document.getElementById('resultsSection');
    const candidatesList = document.getElementById('candidatesList');
    
    if (resultsSection && candidatesList) {
        candidatesList.innerHTML = candidates
            .map(candidate => `
                <div class="candidate-card" data-candidate-id="${candidate.id}">
                    <div class="candidate-poster" style="background-image: url('https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop')"></div>
                    <div class="candidate-info">
                        <div class="candidate-title">${candidate.title}</div>
                        <div class="candidate-confidence">${candidate.confidence}% уверенности</div>
                        <div class="candidate-reason">${candidate.reason}</div>
                    </div>
                    <div class="candidate-actions">
                        <button class="candidate-btn correct-btn" onclick="selectCandidate(${candidate.id}, true)">
                            <i class="fas fa-check"></i>
                            Это он!
                        </button>
                        <button class="candidate-btn wrong-btn" onclick="selectCandidate(${candidate.id}, false)">
                            <i class="fas fa-times"></i>
                            Не он
                        </button>
                    </div>
                </div>
            `)
            .join('');
        
        resultsSection.style.display = 'block';
    }
}

// Выбор кандидата
function selectCandidate(candidateId, isCorrect) {
    if (isCorrect) {
        // Пользователь подтвердил фильм
        showSuccessMessage();
        setTimeout(() => {
            window.location.href = '/results';
        }, 2000);
    } else {
        // Пользователь не подтвердил, показываем уточняющие вопросы
        showClarificationQuestions();
    }
}

// Показать сообщение об успехе
function showSuccessMessage() {
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.innerHTML = `
            <div class="success-message">
                <div class="success-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h3>Отлично! Мы нашли ваш фильм!</h3>
                <p>Переходим к рекомендациям похожих фильмов...</p>
            </div>
        `;
    }
}

// Показать уточняющие вопросы
function showClarificationQuestions() {
    const clarificationSection = document.getElementById('clarificationSection');
    const clarificationQuestions = document.getElementById('clarificationQuestions');
    
    if (clarificationSection && clarificationQuestions) {
        const questions = [
            'В каком году вышел фильм?',
            'Кто главный актер?',
            'В какой стране происходит действие?',
            'Какой жанр у фильма?'
        ];
        
        clarificationQuestions.innerHTML = questions
            .map((question, index) => `
                <div class="clarification-question">
                    <label class="question-label">${question}</label>
                    <input type="text" class="question-input" placeholder="Ваш ответ...">
                </div>
            `)
            .join('');
        
        clarificationSection.style.display = 'block';
    }
}

// Настройка drag and drop
function setupDragAndDrop() {
    const dragDropArea = document.getElementById('dragDropArea');
    if (!dragDropArea) return;
    
    dragDropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dragDropArea.classList.add('drag-over');
    });
    
    dragDropArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dragDropArea.classList.remove('drag-over');
    });
    
    dragDropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dragDropArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
}

// Обработка выбора файла
function handleFileSelect(file) {
    if (!file.type.startsWith('video/')) {
        alert('Пожалуйста, выберите видеофайл');
        return;
    }
    
    // Здесь должна быть логика загрузки и анализа видео
    console.log('Выбран файл:', file.name);
    showLoadingScreen('Анализируем видео...', 'Обрабатываем загруженный файл');
    
    // Имитация анализа
    setTimeout(() => {
        hideLoadingScreen();
        const mockCandidates = [
            { id: 1, title: 'Интерстеллар', confidence: 85, reason: 'По визуальному стилю' },
            { id: 2, title: 'Дюна', confidence: 78, reason: 'По атмосфере' },
            { id: 3, title: 'Бегущий по лезвию 2049', confidence: 65, reason: 'По цветовой палитре' }
        ];
        showResults(mockCandidates);
    }, 3000);
}

// Настройка голосовой записи
function setupVoiceRecording() {
    // Здесь должна быть логика настройки голосовой записи
    console.log('Настройка голосовой записи...');
}

// Переключение голосовой записи
function toggleVoiceRecording() {
    const voiceBtn = document.getElementById('voiceRecordBtn');
    if (!voiceBtn) return;
    
    if (voiceBtn.classList.contains('recording')) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

// Начать запись голоса
function startVoiceRecording() {
    const voiceBtn = document.getElementById('voiceRecordBtn');
    if (voiceBtn) {
        voiceBtn.classList.add('recording');
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i> Остановить запись';
        
        // Здесь должна быть логика записи голоса
        console.log('Начинаем запись голоса...');
    }
}

// Остановить запись голоса
function stopVoiceRecording() {
    const voiceBtn = document.getElementById('voiceRecordBtn');
    if (voiceBtn) {
        voiceBtn.classList.remove('recording');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i> Записать голос';
        
        // Здесь должна быть логика обработки записанного голоса
        console.log('Останавливаем запись голоса...');
        
        // Имитация обработки голоса
        const descriptionInput = document.getElementById('descriptionInput');
        if (descriptionInput) {
            descriptionInput.value = 'Фильм про космос и путешествие во времени';
        }
    }
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

// Скрыть модальное окно
function hideModal() {
    const modal = document.getElementById('movieModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Анимация появления элементов
function animateOnScroll() {
    const elements = document.querySelectorAll('.candidate-card, .clarification-question');
    
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
