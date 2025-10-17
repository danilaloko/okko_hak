"""
Тестовый скрипт для демонстрации системы подбора фильмов
с использованием OpenRouter Structured Outputs
"""

import os
import json
from dotenv import load_dotenv
from movie_recommendation_tool import MovieRecommendationTool

# Загружаем переменные окружения
load_dotenv()


def test_movie_recommendations():
    """Тестирование системы подбора фильмов"""
    
    print("🎬 Тестирование системы подбора фильмов")
    print("=" * 50)
    
    try:
        # Создание системы подбора фильмов
        movie_tool = MovieRecommendationTool()
        print("✅ Система подбора фильмов создана успешно\n")
        
        # Тестовые запросы пользователей
        test_requests = [
            {
                "request": "Хочу посмотреть комедию",
                "description": "Простой запрос по жанру"
            },
            {
                "request": "Покажи фильмы с Леонардо ДиКаприо",
                "description": "Поиск по актеру"
            },
            {
                "request": "Нужен хороший боевик 2020-2023 года",
                "description": "Поиск по жанру и году"
            },
            {
                "request": "Рекомендуй что-то романтическое",
                "description": "Неопределенный запрос"
            },
            {
                "request": "Хочу посмотреть что-то",
                "description": "Очень неопределенный запрос"
            }
        ]
        
        for i, test_case in enumerate(test_requests, 1):
            print(f"--- Тест {i}: {test_case['description']} ---")
            print(f"Запрос: \"{test_case['request']}\"")
            
            try:
                result = movie_tool.recommend_movies(test_case['request'])
                
                if result["success"]:
                    data = result["data"]
                    
                    print(f"✅ Статус: {data.get('status')}")
                    print(f"📝 Сообщение: {data.get('message')}")
                    
                    # Показываем уточняющие вопросы, если есть
                    if data.get('clarification_questions'):
                        print(f"❓ Уточняющие вопросы:")
                        for question in data['clarification_questions']:
                            print(f"   - {question}")
                    
                    # Показываем критерии поиска, если есть
                    if data.get('search_criteria'):
                        criteria = data['search_criteria']
                        print(f"🔍 Критерии поиска:")
                        if criteria.get('genres'):
                            print(f"   Жанры: {', '.join(criteria['genres'])}")
                        if criteria.get('actors'):
                            print(f"   Актеры: {', '.join(criteria['actors'])}")
                        if criteria.get('directors'):
                            print(f"   Режиссеры: {', '.join(criteria['directors'])}")
                        if criteria.get('year_from') or criteria.get('year_to'):
                            year_range = f"{criteria.get('year_from', '?')}-{criteria.get('year_to', '?')}"
                            print(f"   Годы: {year_range}")
                        if criteria.get('content_type'):
                            print(f"   Тип: {criteria['content_type']}")
                    
                    # Показываем рекомендованные фильмы
                    if data.get('recommended_movie_ids'):
                        print(f"🎯 Рекомендованные ID фильмов: {data['recommended_movie_ids']}")
                    
                    # Показываем уверенность
                    if data.get('confidence') is not None:
                        confidence_percent = int(data['confidence'] * 100)
                        print(f"🎯 Уверенность: {confidence_percent}%")
                    
                    print(f"🔄 Итераций: {result.get('iterations', 'N/A')}")
                    
                else:
                    print(f"❌ Ошибка: {result.get('error')}")
                    print(f"📝 Сообщение: {result.get('message')}")
                
            except Exception as e:
                print(f"❌ Исключение: {e}")
            
            print("-" * 60)
        
        print("\n🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("\nПроверьте:")
        print("1. Настроены ли переменные окружения (.env файл)")
        print("2. Доступна ли PostgreSQL база данных")
        print("3. Правильные ли данные для подключения к БД")


def test_structured_output_schema():
    """Тестирование JSON схемы для structured outputs"""
    
    print("\n📋 Тестирование JSON схемы")
    print("=" * 30)
    
    # Пример структурированного ответа
    example_response = {
        "status": "found",
        "message": "Нашел отличные комедии для вас! Рекомендую эти фильмы.",
        "clarification_questions": [],
        "recommended_movie_ids": [123, 456, 789],
        "search_criteria": {
            "genres": ["Комедия"],
            "actors": [],
            "directors": [],
            "year_from": None,
            "year_to": None,
            "content_type": "Фильм"
        },
        "confidence": 0.85
    }
    
    print("Пример структурированного ответа:")
    print(json.dumps(example_response, ensure_ascii=False, indent=2))
    
    # Проверяем соответствие схеме
    required_fields = ["status", "message"]
    optional_fields = [
        "clarification_questions", "recommended_movie_ids", 
        "search_criteria", "confidence"
    ]
    
    print(f"\n✅ Обязательные поля: {required_fields}")
    print(f"📝 Опциональные поля: {optional_fields}")
    
    # Проверяем статусы
    valid_statuses = ["need_more_info", "searching", "found", "not_found"]
    print(f"📊 Валидные статусы: {valid_statuses}")


def interactive_test():
    """Интерактивное тестирование"""
    
    print("\n🎮 Интерактивное тестирование")
    print("=" * 30)
    print("Введите запрос для подбора фильма (или 'quit' для выхода):")
    
    try:
        movie_tool = MovieRecommendationTool()
        
        while True:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'выход']:
                print("👋 До свидания!")
                break
            
            if not user_input:
                continue
            
            print(f"\n🔍 Обрабатываю запрос: \"{user_input}\"")
            
            try:
                result = movie_tool.recommend_movies(user_input)
                
                if result["success"]:
                    data = result["data"]
                    print(f"\n📝 {data.get('message')}")
                    
                    if data.get('recommended_movie_ids'):
                        print(f"🎯 Рекомендованные фильмы: {data['recommended_movie_ids']}")
                    
                    if data.get('clarification_questions'):
                        print("❓ Уточняющие вопросы:")
                        for question in data['clarification_questions']:
                            print(f"   - {question}")
                else:
                    print(f"❌ Ошибка: {result.get('message')}")
                    
            except Exception as e:
                print(f"❌ Ошибка: {e}")
    
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")


def main():
    """Основная функция"""
    
    print("🎬 Movie Recommendation System Test Suite")
    print("=" * 50)
    
    # Проверка переменных окружения
    required_vars = ["OPENROUTER_API_KEY", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        print("Создайте .env файл на основе env_example.txt")
        return
    
    print("✅ Переменные окружения настроены")
    
    # Тестирование схемы
    test_structured_output_schema()
    
    # Основное тестирование
    test_movie_recommendations()
    
    # Интерактивное тестирование
    try:
        interactive_test()
    except KeyboardInterrupt:
        print("\n👋 Тестирование прервано пользователем")


if __name__ == "__main__":
    main()
