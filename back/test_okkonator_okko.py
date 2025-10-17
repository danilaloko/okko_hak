#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для okkonator_okko.py
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from okkonator_okko import (
    load_okko_vector_db, load_model, init_theta, 
    update_theta, filter_and_rank, profile_keywords,
    explain_recommendation
)

def test_okkonator():
    """Тестирует основную функциональность okkonator"""
    print("=== ТЕСТ OKKONATOR ДЛЯ OKKO ===")
    
    # 1. Загрузка данных
    print("\n1. Загрузка данных...")
    df, embeddings, metadata, records_metadata = load_okko_vector_db()
    
    if df is None:
        print("❌ Не удалось загрузить данные")
        return False
    
    print(f"✅ Загружено {len(df)} записей")
    print(f"✅ Размерность эмбеддингов: {embeddings.shape}")
    print(f"✅ Метаданных записей: {len(records_metadata)}")
    
    # 2. Загрузка модели
    print("\n2. Загрузка модели...")
    model_kind, model = load_model()
    
    if model is None:
        print("❌ Не удалось загрузить модель")
        return False
    
    print(f"✅ Модель загружена: {model_kind}")
    
    # 3. Тест профиля пользователя
    print("\n3. Тест профиля пользователя...")
    theta = init_theta()
    
    # Симулируем ответы пользователя
    test_answers = [
        {"targets": {"humor": 1, "genre_comedy": 1}, "value": 2},  # хочу комедию
        {"targets": {"prefer_russian": 1}, "value": 2},  # предпочитаю российское
        {"targets": {"prefer_movies": 1}, "value": 1},  # фильмы больше чем сериалы
    ]
    
    for answer in test_answers:
        update_theta(theta, answer["value"], answer["targets"])
    
    print("✅ Профиль пользователя обновлен")
    
    # 4. Генерация ключевых слов
    print("\n4. Генерация ключевых слов...")
    keywords = profile_keywords(theta)
    print(f"✅ Ключевые слова: {keywords}")
    
    # 5. Поиск рекомендаций
    print("\n5. Поиск рекомендаций...")
    try:
        recs = filter_and_rank(df, embeddings, records_metadata, theta, model_kind, model, top_k=3)
        print(f"✅ Найдено {len(recs)} рекомендаций")
        
        # Показываем результаты
        print("\n=== РЕЗУЛЬТАТЫ ===")
        for i, (idx, row) in enumerate(recs.iterrows(), start=1):
            record_meta = records_metadata[idx] if idx < len(records_metadata) else {}
            
            title = str(row["serial_name"]) if "serial_name" in row else "Неизвестно"
            content_type = record_meta.get("content_type", "")
            country = record_meta.get("country", "")
            genres = ", ".join(record_meta.get("genres", []))
            score = row.get("score", 0)
            
            print(f"{i}. {title}")
            print(f"   Тип: {content_type} | Страна: {country}")
            print(f"   Жанры: {genres}")
            print(f"   Оценка: {score:.3f}")
            
            # Объяснение
            why = explain_recommendation(row, theta, record_meta)
            if why:
                print(f"   Почему: {why}")
            print()
        
        print("✅ Тест успешно завершен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при поиске: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_okkonator()
    if success:
        print("\n🎉 Все тесты прошли успешно!")
    else:
        print("\n💥 Есть ошибки в тестах")
        sys.exit(1)
