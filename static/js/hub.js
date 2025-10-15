/* ==============================
   Hub - Главный экран приложения
   ============================== */

// Глобальные переменные
let userProfile = {
    mood_joy_sadness: 0.5,
    mood_calm_energy: 0.5,
    alone_company: 'alone',
    duration: 'short'
};

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initializeHub();
});

// Основная инициализация хаба
function initializeHub() {
    hideLoadingScreen();
    setupEventListeners();
    loadUserProfile();
    updateSliderValues();
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
    // Слайдеры настроения
    const joySadnessSlider = document.getElementById('joySadnessSlider');
    const calmEnergySlider = document.getElementById('calmEnergySlider');
    
    if (joySadnessSlider) {
        joySadnessSlider.addEventListener('input', (e) => {
            userProfile.mood_joy_sadness = parseFloat(e.target.value);
            updateSliderValues();
            updateProfile();
        });
    }
    
    if (calmEnergySlider) {
        calmEnergySlider.addEventListener('input', (e) => {
            userProfile.mood_calm_energy = parseFloat(e.target.value);
            updateSliderValues();
            updateProfile();
        });
    }
    
    // Переключатели
    const viewingModeRadios = document.querySelectorAll('input[name="viewingMode"]');
    const durationRadios = document.querySelectorAll('input[name="duration"]');
    
    viewingModeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            userProfile.alone_company = e.target.value;
            updateProfile();
        });
    });
    
    durationRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            userProfile.duration = e.target.value;
            updateProfile();
        });
    });
    
    // Карточки режимов
    const modeCards = document.querySelectorAll('.mode-card');
    modeCards.forEach(card => {
        card.addEventListener('click', () => {
            const mode = card.dataset.mode;
            navigateToMode(mode);
        });
    });
    
    // Демо кнопка
    const demoBtn = document.getElementById('demoBtn');
    if (demoBtn) {
        demoBtn.addEventListener('click', () => {
            navigateToDemo();
        });
    }
    
    // Кнопка профиля
    const profileBtn = document.getElementById('profileBtn');
    if (profileBtn) {
        profileBtn.addEventListener('click', () => {
            showProfileInfo();
        });
    }
}

// Загрузка профиля пользователя
async function loadUserProfile() {
    try {
        const response = await fetch('/api/profile');
        if (response.ok) {
            const profile = await response.json();
            userProfile = { ...userProfile, ...profile };
            updateUIFromProfile();
        }
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
    }
}

// Обновление UI из профиля
function updateUIFromProfile() {
    // Обновляем слайдеры
    const joySadnessSlider = document.getElementById('joySadnessSlider');
    const calmEnergySlider = document.getElementById('calmEnergySlider');
    
    if (joySadnessSlider) {
        joySadnessSlider.value = userProfile.mood_joy_sadness;
    }
    if (calmEnergySlider) {
        calmEnergySlider.value = userProfile.mood_calm_energy;
    }
    
    // Обновляем переключатели
    const aloneToggle = document.getElementById('aloneToggle');
    const companyToggle = document.getElementById('companyToggle');
    const shortToggle = document.getElementById('shortToggle');
    const fullToggle = document.getElementById('fullToggle');
    
    if (aloneToggle && companyToggle) {
        if (userProfile.alone_company === 'alone') {
            aloneToggle.checked = true;
        } else {
            companyToggle.checked = true;
        }
    }
    
    if (shortToggle && fullToggle) {
        if (userProfile.duration === 'short') {
            shortToggle.checked = true;
        } else {
            fullToggle.checked = true;
        }
    }
    
    updateSliderValues();
}

// Обновление значений слайдеров
function updateSliderValues() {
    const joySadnessValue = document.getElementById('joySadnessValue');
    const calmEnergyValue = document.getElementById('calmEnergyValue');
    
    if (joySadnessValue) {
        const value = userProfile.mood_joy_sadness;
        if (value < 0.3) {
            joySadnessValue.textContent = 'Грустно';
        } else if (value > 0.7) {
            joySadnessValue.textContent = 'Радостно';
        } else {
            joySadnessValue.textContent = 'Нейтрально';
        }
    }
    
    if (calmEnergyValue) {
        const value = userProfile.mood_calm_energy;
        if (value < 0.3) {
            calmEnergyValue.textContent = 'Спокойно';
        } else if (value > 0.7) {
            calmEnergyValue.textContent = 'Энергично';
        } else {
            calmEnergyValue.textContent = 'Нейтрально';
        }
    }
}

// Обновление профиля на сервере
async function updateProfile() {
    try {
        const response = await fetch('/api/profile/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userProfile)
        });
        
        if (!response.ok) {
            console.error('Ошибка обновления профиля');
        }
    } catch (error) {
        console.error('Ошибка обновления профиля:', error);
    }
}

// Навигация к режиму
function navigateToMode(mode) {
    const modeUrls = {
        'swipe': '/swipe?type=movies',
        'okkonator': '/okkonator',
        'chat': '/chat',
        'identify': '/identify?tab=link'
    };
    
    const url = modeUrls[mode];
    if (url) {
        window.location.href = url;
    }
}

// Навигация к демо
function navigateToDemo() {
    window.location.href = '/demo';
}

// Показать информацию о профиле
function showProfileInfo() {
    // Простое уведомление о профиле
    const profileInfo = `
        Настроение: ${getMoodDescription()}
        Просмотр: ${userProfile.alone_company === 'alone' ? 'В одиночку' : 'Компанией'}
        Длительность: ${userProfile.duration === 'short' ? 'Короткое' : 'Полное'}
    `;
    
    alert(profileInfo);
}

// Получить описание настроения
function getMoodDescription() {
    const joy = userProfile.mood_joy_sadness;
    const energy = userProfile.mood_calm_energy;
    
    if (joy > 0.7 && energy > 0.7) {
        return 'Радостно и энергично';
    } else if (joy > 0.7 && energy < 0.3) {
        return 'Радостно и спокойно';
    } else if (joy < 0.3 && energy > 0.7) {
        return 'Грустно, но энергично';
    } else if (joy < 0.3 && energy < 0.3) {
        return 'Грустно и спокойно';
    } else {
        return 'Нейтрально';
    }
}

// Анимация появления элементов
function animateOnScroll() {
    const elements = document.querySelectorAll('.mode-card, .demo-card');
    
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
