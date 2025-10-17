#!/usr/bin/env python3
"""
Микросервис Swipe - отдельный процесс для обработки свайпов фильмов
Запускается на порту 5002, чтобы не конфликтовать с основными сервисами
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import json
import numpy as np
import pandas as pd
import random

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем логику из okkonator.py
from back.okkonator import (
    load_vector_db, load_movies_fallback, try_load_model, 
    build_item_embeddings, embed_text, cosine_sim, profile_keywords,
    filter_and_rank, init_theta, update_theta, pick_next_question,
    QUESTIONS, LIKERT, AXES, QUESTIONS_MAX, explain
)

app = Flask(__name__)
CORS(app)

# Глобальные переменные для кэширования
df = None
ITEM_EMB = None
model_kind = None
model = None
metadata = None

# Хранилище сессий пользователей
user_sessions = {}

def initialize_swipe_service():
    """Инициализация сервиса свайпов при запуске"""
    global df, ITEM_EMB, model_kind, model, metadata
    
    print("Инициализация сервиса свайпов...")
    
    # Попытка загрузить векторную БД
    df, ITEM_EMB, metadata = load_vector_db("data")
    
    if df is None:
        print("Загружаем данные напрямую из CSV...")
        df = load_movies_fallback("data/IMBD.csv")
        model_kind, model = try_load_model()
        ITEM_EMB = build_item_embeddings(df, model_kind, model)
    else:
        print("Используем предварительно созданную векторную БД")
        model_kind, model = try_load_model()
    
    print(f"Сервис свайпов готов! Загружено {len(df)} фильмов")

def create_user_session():
    """Создать новую сессию пользователя"""
    session_id = f"session_{len(user_sessions)}_{random.randint(1000, 9999)}"
    
    # Инициализируем нулевой вектор пользователя
    user_vector = np.zeros(ITEM_EMB.shape[1]) if ITEM_EMB is not None else np.zeros(384)  # 384 - размер вектора sentence-transformers
    
    user_sessions[session_id] = {
        'user_vector': user_vector,
        'swipe_history': [],
        'liked_movies': [],
        'disliked_movies': [],
        'current_batch': [],
        'batch_index': 0
    }
    return session_id

def get_next_movies_batch(session_id, batch_size=20):
    """Получить следующую партию фильмов для свайпов"""
    if session_id not in user_sessions:
        return None
    
    session = user_sessions[session_id]
    user_vector = session['user_vector']
    
    # Если у нас есть история свайпов, получаем рекомендации на основе вектора пользователя
    if len(session['swipe_history']) > 0 and np.linalg.norm(user_vector) > 0:
        # Вычисляем косинусное сходство с вектором пользователя
        similarities = cosine_sim(user_vector, ITEM_EMB)
        
        # Сортируем фильмы по сходству
        df_with_sim = df.copy()
        df_with_sim['similarity'] = similarities
        recommendations = df_with_sim.sort_values('similarity', ascending=False).head(batch_size * 2)
    else:
        # Если нет истории свайпов, берем случайные фильмы
        recommendations = df.sample(n=min(batch_size * 2, len(df)))
    
    # Добавляем случайные фильмы для разнообразия
    random_movies = df.sample(n=min(batch_size, len(df)))
    
    # Объединяем рекомендации и случайные фильмы
    all_movies = pd.concat([recommendations, random_movies]).drop_duplicates(subset=['title'])
    
    # Выбираем batch_size фильмов
    selected_movies = all_movies.head(batch_size)
    
    # Форматируем для фронтенда
    movies_data = []
    for i, (_, row) in enumerate(selected_movies.iterrows()):
        movie_data = {
            "id": int(row.get('id', i)),
            "title": str(row['title']),
            "year": int(row['year']),
            "genre": str(row['genre']),
            "rating": float(row['rating']),
            "duration": int(row['duration']),
            "votes": f"{int(row['votes']):,}" if 'votes' in row else "N/A",
            "description": str(row.get('description', '')),
            "poster": f"https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop"  # Заглушка
        }
        movies_data.append(movie_data)
    
    session['current_batch'] = movies_data
    session['batch_index'] = 0
    
    return movies_data

def update_profile_from_swipes(session):
    """Обновить вектор пользователя на основе истории свайпов"""
    user_vector = session['user_vector']
    swipe_history = session['swipe_history']
    
    # Обновляем вектор пользователя на основе последних свайпов
    for swipe in swipe_history:
        movie_id = swipe['movie_id']
        action = swipe['action']  # 'like' или 'dislike'
        
        # Определяем вес в зависимости от действия
        weight = 0.1 if action == 'like' else -0.1
        
        # Обновляем вектор пользователя
        user_vector = update_user_vector_from_movie(user_vector, movie_id, weight)
    
    # Сохраняем обновленный вектор
    session['user_vector'] = user_vector

def get_movie_vector(movie_id):
    """Получить вектор фильма из векторной БД"""
    if ITEM_EMB is None or df is None:
        return None
    
    # Находим индекс фильма в DataFrame
    movie_indices = df[df.get('id', df.index) == movie_id].index
    if len(movie_indices) == 0:
        return None
    
    movie_index = movie_indices[0]
    
    # Получаем вектор фильма из эмбеддингов
    if movie_index < len(ITEM_EMB):
        return ITEM_EMB[movie_index]
    
    return None

def update_user_vector_from_movie(user_vector, movie_id, weight):
    """Обновить вектор пользователя на основе вектора фильма"""
    movie_vector = get_movie_vector(movie_id)
    
    if movie_vector is None:
        print(f"Вектор фильма {movie_id} не найден")
        return user_vector
    
    # Добавляем вектор фильма к вектору пользователя с весом
    updated_vector = user_vector + weight * movie_vector
    
    # Нормализуем вектор
    norm = np.linalg.norm(updated_vector)
    if norm > 0:
        updated_vector = updated_vector / norm
    
    return updated_vector

@app.route('/health')
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        "status": "healthy",
        "movies_loaded": len(df) if df is not None else 0,
        "model_ready": model is not None,
        "active_sessions": len(user_sessions)
    })

@app.route('/api/swipe/start', methods=['POST'])
def start_swipe_session():
    """Начать новую сессию свайпов"""
    data = request.get_json()
    batch_size = data.get('batch_size', 20)
    
    session_id = create_user_session()
    movies = get_next_movies_batch(session_id, batch_size)
    
    return jsonify({
        "session_id": session_id,
        "movies": movies,
        "total_movies": len(movies)
    })

@app.route('/api/swipe/action', methods=['POST'])
def handle_swipe_action():
    """Обработать действие свайпа"""
    data = request.get_json()
    session_id = data.get('session_id')
    movie_id = data.get('movie_id')
    action = data.get('action')  # 'like' или 'dislike'
    
    if session_id not in user_sessions:
        return jsonify({"error": "Сессия не найдена"}), 404
    
    session = user_sessions[session_id]
    
    # Получаем вектор фильма для отладки
    movie_vector = get_movie_vector(movie_id)
    
    # Добавляем в историю свайпов
    session['swipe_history'].append({
        'movie_id': movie_id,
        'action': action,
        'timestamp': pd.Timestamp.now().isoformat()
    })
    
    # Добавляем в соответствующий список
    if action == 'like':
        session['liked_movies'].append(movie_id)
    else:
        session['disliked_movies'].append(movie_id)
    
    # Обновляем вектор пользователя
    weight = 0.1 if action == 'like' else -0.1
    session['user_vector'] = update_user_vector_from_movie(session['user_vector'], movie_id, weight)
    
    return jsonify({
        "success": True,
        "profile_updated": True,
        "swipe_count": len(session['swipe_history']),
        "movie_vector_norm": float(np.linalg.norm(movie_vector)) if movie_vector is not None else 0.0,
        "user_vector_norm": float(np.linalg.norm(session['user_vector']))
    })

@app.route('/api/swipe/next-batch', methods=['POST'])
def get_next_batch():
    """Получить следующую партию фильмов"""
    data = request.get_json()
    session_id = data.get('session_id')
    batch_size = data.get('batch_size', 20)
    
    if session_id not in user_sessions:
        return jsonify({"error": "Сессия не найдена"}), 404
    
    movies = get_next_movies_batch(session_id, batch_size)
    
    return jsonify({
        "movies": movies,
        "total_movies": len(movies)
    })

@app.route('/api/swipe/profile', methods=['POST'])
def get_user_profile():
    """Получить профиль пользователя"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    if session_id not in user_sessions:
        return jsonify({"error": "Сессия не найдена"}), 404
    
    session = user_sessions[session_id]
    
    # Создаем простой профиль на основе вектора пользователя
    user_vector = session['user_vector']
    vector_norm = float(np.linalg.norm(user_vector))
    
    return jsonify({
        "user_vector_norm": vector_norm,
        "vector_dimension": len(user_vector),
        "swipe_count": len(session['swipe_history']),
        "liked_count": len(session['liked_movies']),
        "disliked_count": len(session['disliked_movies']),
        "profile_strength": "strong" if vector_norm > 0.5 else "weak" if vector_norm > 0.1 else "empty"
    })

@app.route('/api/swipe/recommendations', methods=['POST'])
def get_swipe_recommendations():
    """Получить рекомендации на основе свайпов"""
    data = request.get_json()
    session_id = data.get('session_id')
    top_k = data.get('top_k', 6)
    
    if session_id not in user_sessions:
        return jsonify({"error": "Сессия не найдена"}), 404
    
    session = user_sessions[session_id]
    user_vector = session['user_vector']
    
    try:
        # Вычисляем косинусное сходство с вектором пользователя
        similarities = cosine_sim(user_vector, ITEM_EMB)
        
        # Сортируем фильмы по сходству
        df_with_sim = df.copy()
        df_with_sim['similarity'] = similarities
        recommendations = df_with_sim.sort_values('similarity', ascending=False).head(top_k)
        
        # Форматируем результат
        result = []
        for i, (_, row) in enumerate(recommendations.iterrows()):
            votes_str = f"{int(row['votes']):,}" if 'votes' in row else "N/A"
            
            movie_data = {
                "id": int(row.get('id', i)),
                "title": str(row['title']),
                "year": int(row['year']),
                "genre": str(row['genre']),
                "rating": float(row['rating']),
                "duration": int(row['duration']),
                "votes": votes_str,
                "description": str(row.get('description', '')),
                "similarity": float(row['similarity']),
                "reason": f"Сходство: {row['similarity']:.3f}",
                "poster": f"https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop"
            }
            result.append(movie_data)
        
        return jsonify({
            "recommendations": result,
            "user_vector_norm": float(np.linalg.norm(user_vector)),
            "total_found": len(result)
        })
        
    except Exception as e:
        print(f"Ошибка при получении рекомендаций: {e}")
        return jsonify({"error": f"Ошибка обработки: {str(e)}"}), 500

@app.route('/api/swipe/session/<session_id>')
def get_session_info(session_id):
    """Получить информацию о сессии"""
    if session_id not in user_sessions:
        return jsonify({"error": "Сессия не найдена"}), 404
    
    session = user_sessions[session_id]
    
    return jsonify({
        "session_id": session_id,
        "swipe_count": len(session['swipe_history']),
        "liked_count": len(session['liked_movies']),
        "disliked_count": len(session['disliked_movies']),
        "current_batch_size": len(session['current_batch']),
        "user_vector_norm": float(np.linalg.norm(session['user_vector']))
    })

@app.route('/api/swipe/debug/movie/<int:movie_id>')
def debug_movie_features(movie_id):
    """Отладочный эндпоинт для просмотра вектора фильма"""
    if df is None or ITEM_EMB is None:
        return jsonify({"error": "База данных не загружена"}), 500
    
    movie = df[df.get('id', df.index) == movie_id]
    if movie.empty:
        return jsonify({"error": "Фильм не найден"}), 404
    
    row = movie.iloc[0]
    movie_vector = get_movie_vector(movie_id)
    
    return jsonify({
        "movie_id": movie_id,
        "title": str(row['title']),
        "genre": str(row['genre']),
        "year": int(row['year']),
        "rating": float(row['rating']),
        "duration": int(row['duration']),
        "description": str(row.get('description', '')),
        "vector_norm": float(np.linalg.norm(movie_vector)) if movie_vector is not None else 0.0,
        "vector_dimension": len(movie_vector) if movie_vector is not None else 0
    })

if __name__ == '__main__':
    print("Запуск микросервиса свайпов...")
    initialize_swipe_service()
    print("Микросервис свайпов запущен на порту 5002")
    app.run(debug=True, host='0.0.0.0', port=5002)
