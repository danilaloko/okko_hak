/* ==============================
   Chat - Экран чата с ИИ
   ============================== */

// Глобальные переменные
let chatHistory = [];
let isTyping = false;
let selectedCelebrity = null;
let celebritiesData = null;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});

// Основная инициализация
function initializeChat() {
    hideLoadingScreen();
    setupEventListeners();
    loadCelebritiesData();
    setupCelebritySelection();
    loadUserProfile();
    setupQuickSuggestions();
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
    
    // Кнопка профиля
    const profileBtn = document.getElementById('profileBtn');
    if (profileBtn) {
        profileBtn.addEventListener('click', () => {
            toggleProfileSidebar();
        });
    }
    
    // Кнопка закрытия сайдбара
    const sidebarClose = document.getElementById('sidebarClose');
    if (sidebarClose) {
        sidebarClose.addEventListener('click', () => {
            hideProfileSidebar();
        });
    }
    
    // Кнопка смены знаменитости
    const changeCelebrityBtn = document.getElementById('changeCelebrityBtn');
    if (changeCelebrityBtn) {
        changeCelebrityBtn.addEventListener('click', () => {
            showCelebritySelector();
        });
    }
    
    // Поле ввода сообщения
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        messageInput.addEventListener('input', () => {
            // Автоматическое изменение размера поля
            messageInput.style.height = 'auto';
            messageInput.style.height = messageInput.scrollHeight + 'px';
        });
    }
    
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // Кнопка голосового ввода
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) {
        voiceBtn.addEventListener('click', toggleVoiceRecording);
    }
    
    // Быстрые подсказки
    const suggestionChips = document.querySelectorAll('.suggestion-chip');
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const suggestion = chip.dataset.suggestion;
            insertSuggestion(suggestion);
        });
    });
    
}

// Загрузка профиля пользователя
async function loadUserProfile() {
    try {
        const response = await fetch('/api/profile');
        if (response.ok) {
            const profile = await response.json();
            updateProfileSidebar(profile);
        }
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
    }
}

// Обновление сайдбара профиля
function updateProfileSidebar(profile) {
    const likedGenres = document.getElementById('likedGenres');
    const dislikedGenres = document.getElementById('dislikedGenres');
    const likedActors = document.getElementById('likedActors');
    
    if (likedGenres && profile.preferences) {
        likedGenres.innerHTML = profile.preferences.liked_genres
            .map(genre => `<span class="profile-tag">${genre}</span>`)
            .join('');
    }
    
    if (dislikedGenres && profile.preferences) {
        dislikedGenres.innerHTML = profile.preferences.disliked_genres
            .map(genre => `<span class="profile-tag">${genre}</span>`)
            .join('');
    }
    
    if (likedActors && profile.preferences) {
        likedActors.innerHTML = profile.preferences.liked_actors
            .map(actor => `<span class="profile-tag">${actor}</span>`)
            .join('');
    }
}

// Настройка быстрых подсказок
function setupQuickSuggestions() {
    const suggestions = [
        'что-то лёгкое',
        '45-60 мин',
        'без насилия',
        'как True Detective',
        'для компании',
        'романтическое',
        'фантастика',
        'комедия',
        'драма',
        'триллер'
    ];
    
    const suggestionsContainer = document.querySelector('.suggestions-chips');
    if (suggestionsContainer) {
        suggestionsContainer.innerHTML = suggestions
            .map(suggestion => `
                <button class="suggestion-chip" data-suggestion="${suggestion}">
                    ${suggestion}
                </button>
            `)
            .join('');
        
        // Добавляем обработчики событий для новых чипов
        const newChips = suggestionsContainer.querySelectorAll('.suggestion-chip');
        newChips.forEach(chip => {
            chip.addEventListener('click', () => {
                const suggestion = chip.dataset.suggestion;
                insertSuggestion(suggestion);
            });
        });
    }
}

// Вставка подсказки в поле ввода
function insertSuggestion(suggestion) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = suggestion;
        messageInput.focus();
        
        // Анимация вставки
        messageInput.style.transform = 'scale(1.02)';
        setTimeout(() => {
            messageInput.style.transform = 'scale(1)';
        }, 200);
    }
}

// Отправка сообщения
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || isTyping) return;
    
    // Проверяем, выбрана ли знаменитость
    if (!selectedCelebrity) {
        addMessageToChat('assistant', 'Пожалуйста, сначала выберите собеседника.');
        return;
    }
    
    // Добавляем сообщение пользователя в чат
    addMessageToChat('user', message);
    
    // Очищаем поле ввода
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Показываем индикатор печати
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                celebrity_id: selectedCelebrity.id
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Скрываем индикатор печати
            hideTypingIndicator();
            
            // Добавляем ответ ассистента
            addMessageToChat('assistant', data.response, selectedCelebrity.id);
            
            // Показываем рекомендации, если есть
            if (data.recommendations && data.recommendations.length > 0) {
                addRecommendationsToChat(data.recommendations);
            }
        }
    } catch (error) {
        console.error('Ошибка отправки сообщения:', error);
        hideTypingIndicator();
        addMessageToChat('assistant', 'Извините, произошла ошибка. Попробуйте еще раз.');
    }
}

// Добавление сообщения в чат
function addMessageToChat(sender, text, celebrityId = null) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    let avatar = '';
    if (sender === 'assistant') {
        if (celebrityId && selectedCelebrity && selectedCelebrity.id === celebrityId) {
            // Иконка для выбранной знаменитости
            const iconMap = {
                'quentin_tarantino': 'fa-film',
                'steven_spielberg': 'fa-magic',
                'leonardo_dicaprio': 'fa-star'
            };
            const icon = iconMap[celebrityId] || 'fa-robot';
            avatar = `<div class="message-avatar"><i class="fas ${icon}"></i></div>`;
        } else {
            avatar = '<div class="message-avatar"><i class="fas fa-robot"></i></div>';
        }
    } else {
        avatar = '<div class="message-avatar"><i class="fas fa-user"></i></div>';
    }
    
    messageDiv.innerHTML = `
        ${avatar}
        <div class="message-content">
            <div class="message-text">${text}</div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // Прокручиваем к последнему сообщению
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Анимация появления
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    setTimeout(() => {
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 100);
}

// Показать индикатор печати
function showTypingIndicator() {
    isTyping = true;
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant-message typing-indicator';
    typingDiv.id = 'typingIndicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Скрыть индикатор печати
function hideTypingIndicator() {
    isTyping = false;
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Добавить рекомендации в чат
function addRecommendationsToChat(recommendations) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message recommendations-message';
    
    const posterImages = [
        'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop',
        'https://images.unsplash.com/photo-1489599803001-0b0b3b0b3b0b?w=200&h=300&fit=crop',
        'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop&auto=format&q=80',
        'https://images.unsplash.com/photo-1489599803001-0b0b3b0b3b0b?w=200&h=300&fit=crop&auto=format&q=80',
        'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop&auto=format&q=80&ixlib=rb-4.0.3',
        'https://images.unsplash.com/photo-1489599803001-0b0b3b0b3b0b?w=200&h=300&fit=crop&auto=format&q=80&ixlib=rb-4.0.3'
    ];
    
    const recommendationsHtml = recommendations
        .map((rec, index) => `
            <div class="recommendation-item">
                <div class="recommendation-poster" style="background-image: url('${posterImages[index % posterImages.length]}')"></div>
                <div class="recommendation-info">
                    <div class="recommendation-title">${rec.title}</div>
                    <div class="recommendation-reason">${rec.reason}</div>
                </div>
                <button class="recommendation-btn" onclick="addToWatchlist('${rec.id}')">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
        `)
        .join('');
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-text">
                <div class="recommendations-header">Рекомендации для вас:</div>
                <div class="recommendations-list">
                    ${recommendationsHtml}
                </div>
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // Прокручиваем к последнему сообщению
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Анимация появления
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    setTimeout(() => {
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 100);
}

// Переключение сайдбара профиля
function toggleProfileSidebar() {
    const sidebar = document.getElementById('profileSidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
}

// Показать сайдбар профиля
function showProfileSidebar() {
    const sidebar = document.getElementById('profileSidebar');
    if (sidebar) {
        sidebar.classList.add('active');
    }
}

// Скрыть сайдбар профиля
function hideProfileSidebar() {
    const sidebar = document.getElementById('profileSidebar');
    if (sidebar) {
        sidebar.classList.remove('active');
    }
}

// Переключение голосового ввода
function toggleVoiceRecording() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (!voiceBtn) return;
    
    if (voiceBtn.classList.contains('recording')) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

// Начать запись голоса
function startVoiceRecording() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) {
        voiceBtn.classList.add('recording');
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        
        // Здесь должна быть логика записи голоса
        console.log('Начинаем запись голоса...');
    }
}

// Остановить запись голоса
function stopVoiceRecording() {
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) {
        voiceBtn.classList.remove('recording');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        
        // Здесь должна быть логика обработки записанного голоса
        console.log('Останавливаем запись голоса...');
    }
}

// Добавить в список просмотра
function addToWatchlist(movieId) {
    console.log('Добавляем в список просмотра:', movieId);
    
    // Визуальная обратная связь
    const button = event.target.closest('.recommendation-btn');
    if (button) {
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.classList.add('added');
        button.disabled = true;
    }
}

// Получить текущее время
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// Анимация появления элементов
function animateOnScroll() {
    const elements = document.querySelectorAll('.suggestion-chip, .message');
    
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

// ==============================
// Функции для работы с выбором знаменитости
// ==============================

// Загрузка данных знаменитостей
async function loadCelebritiesData() {
    try {
        const response = await fetch('/api/celebrities');
        if (response.ok) {
            celebritiesData = await response.json();
        } else {
            // Fallback данные, если API недоступен
            celebritiesData = {
                "quentin_tarantino": {
                    "id": "quentin_tarantino",
                    "display_name": "Квентин Тарантино",
                    "tags": ["режиссёр", "жанровое кино", "криминал"],
                    "communication": {
                        "intro": "Скажи настроение — соберу острые, стильные картины."
                    }
                },
                "steven_spielberg": {
                    "id": "steven_spielberg",
                    "display_name": "Стивен Спилберг",
                    "tags": ["режиссёр", "приключения", "историческая драма"],
                    "communication": {
                        "intro": "Скажи, нужна ли семейность или драматическая глубина — подберу."
                    }
                },
                "leonardo_dicaprio": {
                    "id": "leonardo_dicaprio",
                    "display_name": "Леонардо Ди Каприо",
                    "tags": ["актёр", "драма", "исторические роли"],
                    "communication": {
                        "intro": "Расскажи, что тебя интересует — драма, история или что-то особенное?"
                    }
                }
            };
        }
    } catch (error) {
        console.error('Ошибка загрузки данных знаменитостей:', error);
    }
}

// Настройка выбора знаменитости
function setupCelebritySelection() {
    const celebrityCards = document.querySelectorAll('.celebrity-card');
    
    celebrityCards.forEach(card => {
        card.addEventListener('click', () => {
            const celebrityId = card.dataset.celebrity;
            selectCelebrity(celebrityId);
        });
    });
}

// Выбор знаменитости
function selectCelebrity(celebrityId) {
    if (!celebritiesData || !celebritiesData[celebrityId]) {
        console.error('Данные знаменитости не найдены:', celebrityId);
        return;
    }
    
    selectedCelebrity = celebritiesData[celebrityId];
    
    // Обновляем UI
    updateCelebritySelection(celebrityId);
    updateChatHeader();
    showChatInterface();
    startChatWithCelebrity();
}

// Обновление визуального выбора знаменитости
function updateCelebritySelection(celebrityId) {
    const celebrityCards = document.querySelectorAll('.celebrity-card');
    
    celebrityCards.forEach(card => {
        if (card.dataset.celebrity === celebrityId) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
}

// Обновление заголовка чата
function updateChatHeader() {
    if (!selectedCelebrity) return;
    
    const nameElement = document.getElementById('selectedCelebrityName');
    const descriptionElement = document.getElementById('selectedCelebrityDescription');
    const avatarElement = document.querySelector('.celebrity-avatar-small i');
    
    if (nameElement) {
        nameElement.textContent = selectedCelebrity.display_name;
    }
    
    if (descriptionElement) {
        descriptionElement.textContent = selectedCelebrity.tags.join(', ');
    }
    
    if (avatarElement) {
        // Устанавливаем иконку в зависимости от знаменитости
        const iconMap = {
            'quentin_tarantino': 'fa-film',
            'steven_spielberg': 'fa-magic',
            'leonardo_dicaprio': 'fa-star'
        };
        avatarElement.className = `fas ${iconMap[selectedCelebrity.id] || 'fa-robot'}`;
    }
}

// Показать интерфейс чата
function showChatInterface() {
    const selector = document.getElementById('celebritySelector');
    const chatInterface = document.getElementById('chatInterface');
    
    if (selector && chatInterface) {
        selector.style.display = 'none';
        chatInterface.style.display = 'block';
    }
}

// Показать селектор знаменитости
function showCelebritySelector() {
    const selector = document.getElementById('celebritySelector');
    const chatInterface = document.getElementById('chatInterface');
    
    if (selector && chatInterface) {
        selector.style.display = 'block';
        chatInterface.style.display = 'none';
        
        // Очищаем чат
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        
        // Сбрасываем выбранную знаменитость
        selectedCelebrity = null;
        chatHistory = [];
    }
}

// Начать чат с выбранной знаменитостью
function startChatWithCelebrity() {
    if (!selectedCelebrity) return;
    
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Добавляем приветственное сообщение от знаменитости
    const introMessage = selectedCelebrity.communication?.intro || 
        `Привет! Я ${selectedCelebrity.display_name}. Расскажите, что вы хотите посмотреть?`;
    
    addMessageToChat('assistant', introMessage, selectedCelebrity.id);
}
