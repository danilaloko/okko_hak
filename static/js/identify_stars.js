/* ==============================
   Identify Stars - Чат со звездами
   ============================== */

// Глобальные переменные
let chatHistory = [];
let isTyping = false;
let selectedCharacter = null;

// Данные персонажей
const characters = {
    leonardo: {
        name: "Леонардо ДиКаприо",
        specialty: "Драма, Триллер",
        avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face",
        personality: "Серьезный и вдумчивый актер, специализирующийся на драматических ролях",
        welcomeMessage: "Привет! Я Лео. Люблю глубокие драмы и психологические триллеры. Расскажите, что вас интересует в кино?",
        responses: [
            "Отличный выбор! Я рекомендую 'Начало' - это фильм, который заставляет думать.",
            "Попробуйте 'Волк с Уолл-стрит' - там есть и драма, и юмор.",
            "Для серьезного настроения подойдет 'Выживший' - история о выживании и силе духа."
        ]
    },
    scarlett: {
        name: "Скарлетт Йоханссон",
        specialty: "Фантастика, Боевик",
        avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=100&h=100&fit=crop&crop=face",
        personality: "Сильная и независимая актриса, известная ролями в фантастических фильмах",
        welcomeMessage: "Привет! Я Скарлетт. Обожаю фантастику и боевики. Что хотите посмотреть?",
        responses: [
            "Попробуйте 'Мстители' - там есть все: экшн, юмор и отличная команда!",
            "Для фантастики рекомендую 'Люси' - интересная концепция и динамичный сюжет.",
            "Если хотите что-то более серьезное, посмотрите 'Она' - трогательная история о любви."
        ]
    },
    ryan: {
        name: "Райан Гослинг",
        specialty: "Драма, Романтика",
        avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face",
        personality: "Чувствительный и харизматичный актер, мастер романтических драм",
        welcomeMessage: "Привет! Я Райан. Люблю романтические драмы и истории с душой. Что вас интересует?",
        responses: [
            "Обязательно посмотрите 'Ла-Ла Ленд' - это музыкальная романтика с глубоким смыслом.",
            "Для драмы рекомендую 'Полуночный Париж' - красивая история о времени и любви.",
            "Попробуйте 'Драйв' - стильный триллер с отличной атмосферой."
        ]
    },
    emma: {
        name: "Эмма Стоун",
        specialty: "Комедия, Мюзикл",
        avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face",
        personality: "Яркая и талантливая актриса, известная комедийными и музыкальными ролями",
        welcomeMessage: "Привет! Я Эмма. Обожаю комедии и мюзиклы! Что поднимет вам настроение?",
        responses: [
            "Для хорошего настроения посмотрите 'Ла-Ла Ленд' - там есть и музыка, и романтика!",
            "Попробуйте 'Отличные парни' - веселая комедия с отличным актерским составом.",
            "Рекомендую 'Спайдермен: Возвращение домой' - легкий и веселый супергеройский фильм."
        ]
    },
    tom: {
        name: "Том Харди",
        specialty: "Боевик, Криминал",
        avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&crop=face",
        personality: "Интенсивный и харизматичный актер, специализирующийся на боевиках и криминальных драмах",
        welcomeMessage: "Привет! Я Том. Люблю жесткие боевики и криминальные драмы. Что вас интересует?",
        responses: [
            "Попробуйте 'Безумный Макс: Дорога ярости' - безумный экшн с отличной постановкой.",
            "Для криминала рекомендую 'Легенда' - история о близнецах-гангстерах.",
            "Посмотрите 'Веном' - темный супергеройский фильм с моим участием."
        ]
    },
    natalie: {
        name: "Натали Портман",
        specialty: "Драма, Фантастика",
        avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop&crop=face",
        personality: "Интеллектуальная и многогранная актриса, мастер драматических и фантастических ролей",
        welcomeMessage: "Привет! Я Натали. Люблю умные драмы и фантастику. Что хотите посмотреть?",
        responses: [
            "Рекомендую 'Черный лебедь' - психологическая драма о страсти и совершенстве.",
            "Попробуйте 'Звездные войны' - классическая фантастика с глубоким смыслом.",
            "Для драмы посмотрите 'Леон' - трогательная история о дружбе и защите."
        ]
    }
};

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeIdentifyStars();
});

// Основная инициализация
function initializeIdentifyStars() {
    hideLoadingScreen();
    setupEventListeners();
    setupCharacterSelection();
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
    
    // Кнопка смены персонажа
    const changeCharacterBtn = document.getElementById('changeCharacterBtn');
    if (changeCharacterBtn) {
        changeCharacterBtn.addEventListener('click', () => {
            showCharacterSelector();
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

// Настройка выбора персонажа
function setupCharacterSelection() {
    const characterCards = document.querySelectorAll('.character-card');
    
    characterCards.forEach(card => {
        card.addEventListener('click', () => {
            const characterId = card.dataset.character;
            selectCharacter(characterId);
        });
    });
}

// Выбор персонажа
function selectCharacter(characterId) {
    selectedCharacter = characters[characterId];
    
    if (!selectedCharacter) return;
    
    // Обновляем информацию о выбранном персонаже
    updateSelectedCharacterInfo();
    
    // Скрываем селектор и показываем чат
    hideCharacterSelector();
    showChatContent();
    
    // Обновляем приветственное сообщение
    updateWelcomeMessage();
    
    // Загружаем профиль пользователя
    loadUserProfile();
}

// Обновление информации о выбранном персонаже
function updateSelectedCharacterInfo() {
    const avatar = document.getElementById('selectedCharacterAvatar');
    const name = document.getElementById('selectedCharacterName');
    const specialty = document.getElementById('selectedCharacterSpecialty');
    const assistantAvatar = document.getElementById('assistantAvatar');
    
    if (avatar) avatar.src = selectedCharacter.avatar;
    if (name) name.textContent = selectedCharacter.name;
    if (specialty) specialty.textContent = selectedCharacter.specialty;
    if (assistantAvatar) assistantAvatar.src = selectedCharacter.avatar;
}

// Обновление приветственного сообщения
function updateWelcomeMessage() {
    const welcomeMessage = document.getElementById('welcomeMessage');
    if (welcomeMessage && selectedCharacter) {
        welcomeMessage.textContent = selectedCharacter.welcomeMessage;
    }
}

// Показать селектор персонажей
function showCharacterSelector() {
    const selector = document.getElementById('characterSelector');
    const chatContent = document.getElementById('chatContent');
    
    if (selector) selector.style.display = 'block';
    if (chatContent) chatContent.style.display = 'none';
}

// Скрыть селектор персонажей
function hideCharacterSelector() {
    const selector = document.getElementById('characterSelector');
    if (selector) selector.style.display = 'none';
}

// Показать контент чата
function showChatContent() {
    const chatContent = document.getElementById('chatContent');
    if (chatContent) chatContent.style.display = 'flex';
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
    
    if (!message || isTyping || !selectedCharacter) return;
    
    // Добавляем сообщение пользователя в чат
    addMessageToChat('user', message);
    
    // Очищаем поле ввода
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Показываем индикатор печати
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/chat/stars', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                character: selectedCharacter.name
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Скрываем индикатор печати
            hideTypingIndicator();
            
            // Добавляем ответ персонажа
            addMessageToChat('assistant', data.response);
            
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
function addMessageToChat(sender, text) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = sender === 'assistant' ? 
        `<div class="message-avatar"><img src="${selectedCharacter.avatar}" alt="${selectedCharacter.name}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;"></div>` : 
        '<div class="message-avatar"><i class="fas fa-user"></i></div>';
    
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
            <img src="${selectedCharacter.avatar}" alt="${selectedCharacter.name}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">
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
            <img src="${selectedCharacter.avatar}" alt="${selectedCharacter.name}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">
        </div>
        <div class="message-content">
            <div class="message-text">
                <div class="recommendations-header">Рекомендации от ${selectedCharacter.name}:</div>
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
