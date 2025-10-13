from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import random

app = Flask(__name__)
CORS(app)

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

@app.route('/')
def index():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


