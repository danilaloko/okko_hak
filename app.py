from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import random
import requests

app = Flask(__name__)
CORS(app)

# URL микросервиса Окконатора
OKKONATOR_SERVICE_URL = "http://localhost:5001"

# Глобальные переменные для состояния пользователя
user_profile = {
    'mood_joy_sadness': 0.5,  # 0 = грусть, 1 = радость
    'mood_calm_energy': 0.5,  # 0 = спокойствие, 1 = энергия
    'alone_company': 'alone',  # 'alone' или 'company'
    'duration': 'short',  # 'short' или 'full'
    'preferences': {
        'liked_movies': [],
        'disliked_movies': [],
        'liked_genres': [],
        'disliked_genres': [],
        'liked_actors': [],
        'disliked_actors': []
    },
    'okkonator_answers': [],
    'okkonator_theta': {},  # Профиль Окконатора
    'chat_history': [],
    'identified_movies': []
}

# История подборок пользователя
selection_history = [
    {
        'id': 1,
        'date': '2024-01-15',
        'service': 'Okko',
        'method': 'Свайпы',
        'movies': [
            {'id': 1, 'title': 'Интерстеллар', 'poster': 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=200&h=300&fit=crop'},
            {'id': 2, 'title': 'Дюна', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'},
            {'id': 3, 'title': 'Темный рыцарь', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'}
        ]
    },
    {
        'id': 2,
        'date': '2024-01-10',
        'service': 'Netflix',
        'method': 'Окконатор',
        'movies': [
            {'id': 4, 'title': 'Начало', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'},
            {'id': 5, 'title': 'Матрица', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'},
            {'id': 6, 'title': 'Бегущий по лезвию 2049', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'}
        ]
    },
    {
        'id': 3,
        'date': '2024-01-05',
        'service': 'YouTube',
        'method': 'Чат',
        'movies': [
            {'id': 1, 'title': 'Интерстеллар', 'poster': 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=200&h=300&fit=crop'},
            {'id': 3, 'title': 'Темный рыцарь', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'}
        ]
    },
    {
        'id': 4,
        'date': '2024-01-01',
        'service': 'Кинопоиск',
        'method': 'Помощь от звезд',
        'movies': [
            {'id': 2, 'title': 'Дюна', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'},
            {'id': 4, 'title': 'Начало', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'},
            {'id': 5, 'title': 'Матрица', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'},
            {'id': 6, 'title': 'Бегущий по лезвию 2049', 'poster': 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=200&h=300&fit=crop'}
        ]
    }
]

# Примеры данных фильмов
movies_data = [
    {
        "id": 1,
        "title": "Интерстеллар",
        "year": 2014,
        "genre": "Фантастика, Драма",
        "rating": 8.6,
        "description": "Когда засуха, пыльные бури и вымирание угрожают человечеству, группа астронавтов отправляется через червоточину в космосе, чтобы найти новую планету для жизни.",
        "poster": "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=400&h=600&fit=crop",
        "director": "Кристофер Нолан"
    },
    {
        "id": 2,
        "title": "Бегущий по лезвию 2049",
        "year": 2017,
        "genre": "Фантастика, Триллер",
        "rating": 8.0,
        "description": "Молодой офицер полиции раскрывает секрет, который может погрузить общество в хаос. Его поиски приводят к исчезнувшему Рику Декарду.",
        "poster": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop",
        "director": "Дени Вильнёв"
    },
    {
        "id": 3,
        "title": "Дюна",
        "year": 2021,
        "genre": "Фантастика, Приключения",
        "rating": 8.0,
        "description": "Пол Атрейдес, талантливый и многообещающий молодой человек, рожденный с великой судьбой, которую он не может понять, должен отправиться на самую опасную планету во вселенной.",
        "poster": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop",
        "director": "Дени Вильнёв"
    },
    {
        "id": 4,
        "title": "Темный рыцарь",
        "year": 2008,
        "genre": "Боевик, Криминал",
        "rating": 9.0,
        "description": "Когда угроза, известная как Джокер, сеет хаос и беспорядок среди жителей Готэма, Бэтмен должен принять одно из величайших психологических и физических испытаний.",
        "poster": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop",
        "director": "Кристофер Нолан"
    },
    {
        "id": 5,
        "title": "Начало",
        "year": 2010,
        "genre": "Фантастика, Триллер",
        "rating": 8.8,
        "description": "Вор, который проникает в сны людей, получает шанс искупить свою вину, выполнив последнее задание: внедрить идею в подсознание.",
        "poster": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop",
        "director": "Кристофер Нолан"
    },
    {
        "id": 6,
        "title": "Матрица",
        "year": 1999,
        "genre": "Фантастика, Боевик",
        "rating": 8.7,
        "description": "Компьютерный хакер узнает от таинственных повстанцев о истинной природе его реальности и своей роли в войне против ее контролеров.",
        "poster": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop",
        "director": "Лана и Лилли Вачовски"
    }
]

# Глобальная переменная для отслеживания текущего индекса фильма
current_movie_index = 0

# Главный хаб
@app.route('/')
def hub():
    return render_template('hub.html')

# Режимы
@app.route('/swipe')
def swipe():
    swipe_type = request.args.get('type', 'movies')
    return render_template('swipe.html', swipe_type=swipe_type)

@app.route('/okkonator')
def okkonator():
    return render_template('okkonator.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/identify')
def identify():
    tab = request.args.get('tab', 'link')
    return render_template('identify.html', tab=tab)

@app.route('/identify-stars')
def identify_stars():
    return render_template('identify_stars.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/group-survey')
def group_survey():
    return render_template('group_survey.html')

@app.route('/api/movies')
def get_movies():
    """Получить список всех фильмов"""
    return jsonify(movies_data)

@app.route('/api/current-movie')
def get_current_movie():
    """Получить текущий фильм для показа"""
    global current_movie_index
    if current_movie_index < len(movies_data):
        return jsonify(movies_data[current_movie_index])
    else:
        return jsonify({"message": "Больше фильмов нет"}), 404

@app.route('/api/swipe', methods=['POST'])
def swipe_movie():
    """Обработать свайп фильма"""
    global current_movie_index
    data = request.get_json()
    action = data.get('action')  # 'like' или 'dislike'
    
    if current_movie_index < len(movies_data):
        movie = movies_data[current_movie_index]
        current_movie_index += 1
        
        # Здесь можно добавить логику сохранения предпочтений
        print(f"Пользователь {action} фильм: {movie['title']}")
        
        return jsonify({
            "success": True,
            "action": action,
            "movie": movie,
            "next_available": current_movie_index < len(movies_data)
        })
    else:
        return jsonify({"message": "Больше фильмов нет"}), 404

@app.route('/api/reset')
def reset_movies():
    """Сбросить индекс фильмов"""
    global current_movie_index
    current_movie_index = 0
    return jsonify({"success": True, "message": "Индекс сброшен"})

# API для настроек профиля
@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    """Обновить настройки профиля"""
    global user_profile
    data = request.get_json()
    
    if 'mood_joy_sadness' in data:
        user_profile['mood_joy_sadness'] = float(data['mood_joy_sadness'])
    if 'mood_calm_energy' in data:
        user_profile['mood_calm_energy'] = float(data['mood_calm_energy'])
    if 'alone_company' in data:
        user_profile['alone_company'] = data['alone_company']
    if 'duration' in data:
        user_profile['duration'] = data['duration']
    
    return jsonify({"success": True, "profile": user_profile})

@app.route('/api/profile')
def get_profile():
    """Получить текущий профиль"""
    return jsonify(user_profile)

# API для свайпов
@app.route('/api/swipe/action', methods=['POST'])
def swipe_action():
    """Обработать действие свайпа"""
    global user_profile
    data = request.get_json()
    action = data.get('action')  # 'like', 'dislike', 'superlike'
    content = data.get('content')
    content_type = data.get('type', 'movies')
    
    if action == 'like' or action == 'superlike':
        if content_type == 'movies':
            user_profile['preferences']['liked_movies'].append(content['id'])
        elif content_type == 'genres':
            user_profile['preferences']['liked_genres'].append(content)
        elif content_type == 'actors':
            user_profile['preferences']['liked_actors'].append(content)
    elif action == 'dislike':
        if content_type == 'movies':
            user_profile['preferences']['disliked_movies'].append(content['id'])
        elif content_type == 'genres':
            user_profile['preferences']['disliked_genres'].append(content)
        elif content_type == 'actors':
            user_profile['preferences']['disliked_actors'].append(content)
    
    return jsonify({"success": True, "profile": user_profile})

# API для Окконатора - прокси к микросервису
@app.route('/api/okkonator/question', methods=['POST'])
def get_okkonator_question():
    """Получить следующий вопрос для Окконатора"""
    try:
        # Получаем данные от клиента
        data = request.get_json()
        theta = data.get('theta', {})
        asked_ids = data.get('asked_ids', [])
        
        print(f"Запрос вопроса: theta={theta}, asked_ids={asked_ids}")
        
        response = requests.post(f"{OKKONATOR_SERVICE_URL}/api/okkonator/next-question", 
                               json={"theta": theta, "asked_ids": asked_ids})
        
        print(f"Ответ микросервиса: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Данные от микросервиса: {data}")
            return jsonify(data)
        else:
            print(f"Ошибка микросервиса: {response.text}")
            return jsonify({"error": "Сервис Окконатора недоступен"}), 500
            
    except requests.exceptions.ConnectionError:
        print("Ошибка подключения к микросервису")
        return jsonify({"error": "Микросервис Окконатора не запущен"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500

@app.route('/api/okkonator/answer', methods=['POST'])
def submit_okkonator_answer():
    """Отправить ответ на вопрос Окконатора"""
    try:
        data = request.get_json()
        answer = data.get('answer')  # 'yes', 'no', 'maybe', 'probably_yes', 'probably_no'
        question_id = data.get('question_id')
        
        print(f"Обработка ответа: {answer} для вопроса {question_id}")
        
        # Конвертируем ответ в числовое значение
        answer_mapping = {
            'no': -2,
            'probably_no': -1, 
            'maybe': 0,
            'probably_yes': 1,
            'yes': 2
        }
        answer_value = answer_mapping.get(answer, 0)
        
        # Получаем профиль от клиента
        theta = data.get('theta', {})
        
        print(f"Профиль от клиента: {theta}")
        print(f"Значение ответа: {answer_value}")
        
        # Отправляем в микросервис
        response = requests.post(f"{OKKONATOR_SERVICE_URL}/api/okkonator/answer",
                               json={
                                   "theta": theta,
                                   "answer_value": answer_value,
                                   "question_id": question_id
                               })
        
        print(f"Ответ микросервиса на ответ: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Обновленный профиль: {data.get('theta', {})}")
            
            return jsonify({"success": True, "theta": data['theta']})
        else:
            print(f"Ошибка микросервиса: {response.text}")
            return jsonify({"error": "Ошибка обработки ответа"}), 500
            
    except requests.exceptions.ConnectionError:
        print("Ошибка подключения к микросервису")
        return jsonify({"error": "Микросервис Окконатора не запущен"}), 500
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500

@app.route('/api/okkonator/recommendations', methods=['POST'])
def get_okkonator_recommendations():
    """Получить рекомендации от Окконатора"""
    try:
        data = request.get_json()
        top_k = data.get('top_k', 6)
        theta = data.get('theta', {})  # Получаем профиль от клиента
        
        print(f"Запрос рекомендаций: theta={theta}, top_k={top_k}")
        
        response = requests.post(f"{OKKONATOR_SERVICE_URL}/api/okkonator/recommendations",
                               json={"theta": theta, "top_k": top_k})
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Ошибка получения рекомендаций"}), 500
            
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Микросервис Окконатора не запущен"}), 500
    except Exception as e:
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500

# API для чата
@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """Отправить сообщение в чат"""
    data = request.get_json()
    message = data.get('message')
    
    # Простая логика ответа (в реальном приложении здесь будет AI)
    responses = [
        "Понял! Рекомендую посмотреть 'Интерстеллар' - отличная фантастика с глубоким сюжетом.",
        "Учитывая ваши предпочтения, предлагаю 'Дюна' - эпическая фантастическая сага.",
        "Попробуйте 'Темный рыцарь' - это классика жанра с отличной актерской игрой.",
        "Рекомендую 'Начало' - сложный, но увлекательный фильм с необычным сюжетом."
    ]
    
    response = random.choice(responses)
    
    user_profile['chat_history'].append({
        'user': message,
        'assistant': response,
        'timestamp': 'now'
    })
    
    # Простая логика рекомендаций на основе сообщения
    recommendations = []
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['короткое', 'короткий', 'быстро', '45', '60', 'минут']):
        recommendations = [
            {"id": 1, "title": "Интерстеллар", "reason": "Эпическая фантастика, 169 минут"},
            {"id": 2, "title": "Дюна", "reason": "Космическая сага, 155 минут"},
            {"id": 3, "title": "Темный рыцарь", "reason": "Классика жанра, 152 минуты"}
        ]
    elif any(word in message_lower for word in ['легкое', 'лёгкое', 'комедия', 'веселое']):
        recommendations = [
            {"id": 4, "title": "Барби", "reason": "Яркая комедия с глубоким смыслом"},
            {"id": 5, "title": "Топ Ган: Мэверик", "reason": "Захватывающий боевик с юмором"},
            {"id": 6, "title": "Начало", "reason": "Умная фантастика с необычным сюжетом"}
        ]
    else:
        recommendations = [
            {"id": 1, "title": "Интерстеллар", "reason": "Соответствует вашим предпочтениям"},
            {"id": 2, "title": "Дюна", "reason": "Эпическая фантастика"},
            {"id": 3, "title": "Темный рыцарь", "reason": "Классика жанра"}
        ]
    
    return jsonify({
        "success": True,
        "response": response,
        "recommendations": recommendations
    })

# API для чата со звездами
@app.route('/api/chat/stars', methods=['POST'])
def chat_stars():
    """Отправить сообщение в чат со звездой"""
    data = request.get_json()
    message = data.get('message')
    character = data.get('character')
    
    # Персонализированные ответы для каждой звезды
    character_responses = {
        "Леонардо ДиКаприо": [
            "Отличный выбор! Я рекомендую 'Начало' - это фильм, который заставляет думать.",
            "Попробуйте 'Волк с Уолл-стрит' - там есть и драма, и юмор.",
            "Для серьезного настроения подойдет 'Выживший' - история о выживании и силе духа."
        ],
        "Скарлетт Йоханссон": [
            "Попробуйте 'Мстители' - там есть все: экшн, юмор и отличная команда!",
            "Для фантастики рекомендую 'Люси' - интересная концепция и динамичный сюжет.",
            "Если хотите что-то более серьезное, посмотрите 'Она' - трогательная история о любви."
        ],
        "Райан Гослинг": [
            "Обязательно посмотрите 'Ла-Ла Ленд' - это музыкальная романтика с глубоким смыслом.",
            "Для драмы рекомендую 'Полуночный Париж' - красивая история о времени и любви.",
            "Попробуйте 'Драйв' - стильный триллер с отличной атмосферой."
        ],
        "Эмма Стоун": [
            "Для хорошего настроения посмотрите 'Ла-Ла Ленд' - там есть и музыка, и романтика!",
            "Попробуйте 'Отличные парни' - веселая комедия с отличным актерским составом.",
            "Рекомендую 'Спайдермен: Возвращение домой' - легкий и веселый супергеройский фильм."
        ],
        "Том Харди": [
            "Попробуйте 'Безумный Макс: Дорога ярости' - безумный экшн с отличной постановкой.",
            "Для криминала рекомендую 'Легенда' - история о близнецах-гангстерах.",
            "Посмотрите 'Веном' - темный супергеройский фильм с моим участием."
        ],
        "Натали Портман": [
            "Рекомендую 'Черный лебедь' - психологическая драма о страсти и совершенстве.",
            "Попробуйте 'Звездные войны' - классическая фантастика с глубоким смыслом.",
            "Для драмы посмотрите 'Леон' - трогательная история о дружбе и защите."
        ]
    }
    
    # Получаем ответ от выбранного персонажа
    responses = character_responses.get(character, ["Отличный выбор! Рекомендую посмотреть что-то интересное."])
    response = random.choice(responses)
    
    user_profile['chat_history'].append({
        'user': message,
        'assistant': response,
        'character': character,
        'timestamp': 'now'
    })
    
    # Персонализированные рекомендации на основе звезды
    recommendations = []
    message_lower = message.lower()
    
    if character == "Леонардо ДиКаприо":
        recommendations = [
            {"id": 1, "title": "Начало", "reason": "Сложная драма с элементами фантастики"},
            {"id": 2, "title": "Выживший", "reason": "Эпическая история о выживании"},
            {"id": 3, "title": "Волк с Уолл-стрит", "reason": "Драма с элементами комедии"}
        ]
    elif character == "Скарлетт Йоханссон":
        recommendations = [
            {"id": 4, "title": "Мстители", "reason": "Эпический супергеройский боевик"},
            {"id": 5, "title": "Люси", "reason": "Фантастический триллер с необычным сюжетом"},
            {"id": 6, "title": "Она", "reason": "Трогательная драма о любви и технологиях"}
        ]
    elif character == "Райан Гослинг":
        recommendations = [
            {"id": 7, "title": "Ла-Ла Ленд", "reason": "Музыкальная романтика с глубоким смыслом"},
            {"id": 8, "title": "Драйв", "reason": "Стильный триллер с отличной атмосферой"},
            {"id": 9, "title": "Полуночный Париж", "reason": "Романтическая драма о времени"}
        ]
    elif character == "Эмма Стоун":
        recommendations = [
            {"id": 10, "title": "Ла-Ла Ленд", "reason": "Музыкальная комедия с романтикой"},
            {"id": 11, "title": "Отличные парни", "reason": "Веселая комедия с отличным актерским составом"},
            {"id": 12, "title": "Спайдермен", "reason": "Легкий супергеройский фильм"}
        ]
    elif character == "Том Харди":
        recommendations = [
            {"id": 13, "title": "Безумный Макс", "reason": "Безумный экшн с отличной постановкой"},
            {"id": 14, "title": "Легенда", "reason": "Криминальная драма о близнецах-гангстерах"},
            {"id": 15, "title": "Веном", "reason": "Темный супергеройский фильм"}
        ]
    elif character == "Натали Портман":
        recommendations = [
            {"id": 16, "title": "Черный лебедь", "reason": "Психологическая драма о страсти"},
            {"id": 17, "title": "Звездные войны", "reason": "Классическая фантастика"},
            {"id": 18, "title": "Леон", "reason": "Трогательная драма о дружбе"}
        ]
    else:
        recommendations = [
            {"id": 1, "title": "Интерстеллар", "reason": "Соответствует вашим предпочтениям"},
            {"id": 2, "title": "Дюна", "reason": "Эпическая фантастика"},
            {"id": 3, "title": "Темный рыцарь", "reason": "Классика жанра"}
        ]
    
    return jsonify({
        "success": True,
        "response": response,
        "recommendations": recommendations
    })

# API для идентификации фильмов
@app.route('/api/identify/url', methods=['POST'])
def identify_by_url():
    """Идентифицировать фильм по URL"""
    data = request.get_json()
    url = data.get('url')
    
    # Имитация анализа URL
    candidates = [
        {"id": 1, "title": "Интерстеллар", "confidence": 85, "reason": "По трейлеру"},
        {"id": 2, "title": "Дюна", "confidence": 78, "reason": "По визуальному стилю"},
        {"id": 3, "title": "Бегущий по лезвию 2049", "confidence": 65, "reason": "По атмосфере"}
    ]
    
    return jsonify({
        "success": True,
        "candidates": candidates
    })

@app.route('/api/identify/description', methods=['POST'])
def identify_by_description():
    """Идентифицировать фильм по описанию"""
    data = request.get_json()
    description = data.get('description')
    
    # Имитация анализа описания
    candidates = [
        {"id": 1, "title": "Интерстеллар", "confidence": 90, "reason": "Космическая драма о путешествии"},
        {"id": 2, "title": "Дюна", "confidence": 75, "reason": "Эпическая фантастика"},
        {"id": 3, "title": "Начало", "confidence": 60, "reason": "Сложный сюжет"}
    ]
    
    return jsonify({
        "success": True,
        "candidates": candidates
    })

# API для результатов
@app.route('/api/results')
def get_results():
    """Получить рекомендации на основе профиля"""
    # Простая логика рекомендаций
    recommendations = []
    
    # Фильтруем по предпочтениям
    for movie in movies_data:
        score = 0
        if movie['id'] in user_profile['preferences']['liked_movies']:
            score += 100
        if movie['id'] in user_profile['preferences']['disliked_movies']:
            score -= 100
        
        # Учитываем настроение
        if user_profile['mood_joy_sadness'] > 0.7:  # Радостное настроение
            if 'Комедия' in movie['genre']:
                score += 20
        else:  # Грустное настроение
            if 'Драма' in movie['genre']:
                score += 20
        
        if score > 0:
            recommendations.append({
                **movie,
                'score': score,
                'reason': f"Подходит по настроению и предпочтениям"
            })
    
    # Сортируем по релевантности
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        "recommendations": recommendations[:10],
        "profile": user_profile
    })

# API для истории подборок
@app.route('/api/history')
def get_selection_history():
    """Получить историю подборок пользователя"""
    return jsonify({
        "history": selection_history,
        "total": len(selection_history)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)



