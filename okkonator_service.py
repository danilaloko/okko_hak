#!/usr/bin/env python3
"""
Микросервис Окконатора - отдельный процесс для обработки рекомендаций фильмов
Запускается на порту 5001, чтобы не конфликтовать с основным Flask приложением
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import json
import numpy as np
import pandas as pd

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем логику из okkonator.py
from back.okkonator import (
    load_vector_db, load_movies_fallback, try_load_model, 
    build_item_embeddings, embed_text, cosine_sim, profile_keywords,
    filter_and_rank, init_theta, update_theta, pick_next_question,
    QUESTIONS, LIKERT, AXES, explain
)

app = Flask(__name__)
CORS(app)

# Глобальные переменные для кэширования
df = None
ITEM_EMB = None
model_kind = None
model = None
metadata = None

def initialize_okkonator():
    """Инициализация Окконатора при запуске сервиса"""
    global df, ITEM_EMB, model_kind, model, metadata
    
    print("Инициализация Окконатора...")
    
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
    
    print(f"Окконатор готов! Загружено {len(df)} фильмов")

@app.route('/health')
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        "status": "healthy",
        "movies_loaded": len(df) if df is not None else 0,
        "model_ready": model is not None
    })

@app.route('/api/okkonator/questions')
def get_questions():
    """Получить список всех вопросов"""
    return jsonify({
        "questions": QUESTIONS,
        "total": len(QUESTIONS)
    })

@app.route('/api/okkonator/next-question', methods=['POST'])
def get_next_question():
    """Получить следующий вопрос на основе текущего профиля"""
    data = request.get_json()
    theta = data.get('theta', {})
    asked_ids = data.get('asked_ids', [])
    
    # Инициализируем theta если пустой
    if not theta:
        theta = init_theta()
    
    question = pick_next_question(theta, asked_ids)
    
    if question is None:
        return jsonify({"message": "Вопросы закончились"})
    
    # Вычисляем уверенность профиля
    confidence = int(100 * len(asked_ids) / len(QUESTIONS))
    
    return jsonify({
        "question": question,
        "confidence": confidence,
        "theta": theta
    })

@app.route('/api/okkonator/answer', methods=['POST'])
def submit_answer():
    """Обработать ответ пользователя"""
    data = request.get_json()
    theta = data.get('theta', {})
    answer_value = data.get('answer_value')  # -2, -1, 0, 1, 2
    question_id = data.get('question_id')
    asked_ids = data.get('asked_ids', [])
    
    # Инициализируем theta если пустой
    if not theta:
        theta = init_theta()
    
    # Находим вопрос
    question = None
    for q in QUESTIONS:
        if q['id'] == question_id:
            question = q
            break
    
    if not question:
        return jsonify({"error": "Вопрос не найден"}), 400
    
    # Обновляем профиль
    if answer_value != 0:
        update_theta(theta, answer_value, question['targets'])
    
    # Вычисляем уверенность на основе количества заданных вопросов
    confidence = int(100 * len(asked_ids) / len(QUESTIONS))
    
    return jsonify({
        "theta": theta,
        "confidence": confidence,
        "updated": True
    })

@app.route('/api/okkonator/recommendations', methods=['POST'])
def get_recommendations():
    """Получить рекомендации на основе профиля"""
    data = request.get_json()
    theta = data.get('theta', {})
    top_k = data.get('top_k', 6)
    
    if df is None or ITEM_EMB is None:
        return jsonify({"error": "Сервис не инициализирован"}), 500
    
    # Инициализируем theta если пустой
    if not theta:
        theta = init_theta()
    
    try:
        # Получаем рекомендации
        recommendations = filter_and_rank(df, ITEM_EMB, theta, model_kind, model, top_k)
        
        # Форматируем результат
        result = []
        for i, (_, row) in enumerate(recommendations.iterrows()):
            why = explain(row, theta)
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
                "score": float(row.get('score', 0)),
                "reason": why,
                "poster": f"https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=400&h=600&fit=crop"  # Заглушка
            }
            result.append(movie_data)
        
        return jsonify({
            "recommendations": result,
            "profile": theta,
            "total_found": len(result)
        })
        
    except Exception as e:
        print(f"Ошибка при получении рекомендаций: {e}")
        return jsonify({"error": f"Ошибка обработки: {str(e)}"}), 500

@app.route('/api/okkonator/profile-keywords', methods=['POST'])
def get_profile_keywords():
    """Получить ключевые слова профиля"""
    data = request.get_json()
    theta = data.get('theta', {})
    
    keywords = profile_keywords(theta)
    
    return jsonify({
        "keywords": keywords,
        "profile": theta
    })

@app.route('/api/okkonator/explain-recommendation', methods=['POST'])
def explain_recommendation():
    """Объяснить конкретную рекомендацию"""
    data = request.get_json()
    theta = data.get('theta', {})
    movie_id = data.get('movie_id')
    
    if df is None:
        return jsonify({"error": "Сервис не инициализирован"}), 500
    
    # Находим фильм
    movie = df[df.get('id', df.index) == movie_id]
    if movie.empty:
        return jsonify({"error": "Фильм не найден"}), 404
    
    row = movie.iloc[0]
    explanation = explain(row, theta)
    
    return jsonify({
        "explanation": explanation,
        "movie": {
            "title": str(row['title']),
            "genre": str(row['genre']),
            "year": int(row['year']),
            "rating": float(row['rating'])
        }
    })

if __name__ == '__main__':
    print("Запуск микросервиса Окконатора...")
    initialize_okkonator()
    print("Микросервис Окконатора запущен на порту 5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
