"""
Улучшенный тест системы подбора фильмов с обработкой ошибок
"""

import os
import json
from dotenv import load_dotenv
from movie_recommendation_tool import MovieRecommendationTool

# Загружаем переменные окружения
load_dotenv()


def test_with_different_models():
    """Тестирование с разными моделями"""
    
    # Модели для тестирования (от более надежных к менее)
    models_to_try = [
        "anthropic/claude-haiku-4.5",
        "qwen/qwen3-vl-8b-thinking",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.0-flash-001",
        "meta-llama/llama-3.1-8b-instruct"
    ]
    
    test_request = "Хочу посмотреть комедию"
    
    print("🎬 Тестирование с разными моделями")
    print("=" * 40)
    
    for model in models_to_try:
        print(f"\n--- Тестирование модели: {model} ---")
        
        try:
            movie_tool = MovieRecommendationTool()
            result = movie_tool.recommend_movies(test_request, model=model)
            
            if result["success"]:
                data = result["data"]
                print(f"✅ Успех с моделью {model}")
                print(f"📝 Статус: {data.get('status')}")
                print(f"💬 Сообщение: {data.get('message')}")
                
                if data.get('recommended_movie_ids'):
                    print(f"🎯 Фильмы: {data['recommended_movie_ids']}")
                
                if data.get('clarification_questions'):
                    print(f"❓ Вопросы: {len(data['clarification_questions'])}")
                
                return model  # Возвращаем рабочую модель
            else:
                print(f"❌ Ошибка с моделью {model}: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Исключение с моделью {model}: {e}")
    
    return None


def test_simple_request():
    """Простой тест без structured outputs"""
    
    print("\n🔧 Простой тест без structured outputs")
    print("=" * 40)
    
    try:
        from openrouter_with_db_tools import OpenRouterWithDBTools
        
        client = OpenRouterWithDBTools()
        
        # Простой запрос к базе данных
        response = client.simple_db_query("Покажи все таблицы в базе данных")
        print(f"✅ Ответ от БД: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка простого запроса: {e}")
        return False


def test_database_direct():
    """Прямое тестирование базы данных"""
    
    print("\n🗄️ Прямое тестирование базы данных")
    print("=" * 40)
    
    try:
        from database_tool import DatabaseTool
        
        db_tool = DatabaseTool()
        
        # Тест 1: Список таблиц
        print("--- Список таблиц ---")
        tables_result = db_tool.get_available_tables()
        if tables_result["success"]:
            print(f"✅ Найдено таблиц: {len(tables_result['data'])}")
            for table in tables_result["data"][:3]:
                print(f"   - {table['table_name']}")
        else:
            print(f"❌ Ошибка: {tables_result['error']}")
        
        # Тест 2: Поиск фильмов
        print("\n--- Поиск фильмов ---")
        movies_result = db_tool.execute_sql_query("""
            SELECT title_id, serial_name, content_type 
            FROM title 
            WHERE content_type = 'Фильм' 
            LIMIT 5
        """)
        if movies_result["success"]:
            print(f"✅ Найдено фильмов: {len(movies_result['data'])}")
            for movie in movies_result["data"]:
                print(f"   - {movie['serial_name']} (ID: {movie['title_id']})")
        else:
            print(f"❌ Ошибка: {movies_result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False


def test_fallback_mode():
    """Тест fallback режима (без structured outputs)"""
    
    print("\n🔄 Тест fallback режима")
    print("=" * 30)
    
    try:
        movie_tool = MovieRecommendationTool()
        
        # Принудительно используем fallback режим
        test_request = "Хочу посмотреть комедию"
        
        # Модифицируем метод для принудительного fallback
        original_method = movie_tool._send_structured_request
        movie_tool._send_structured_request = movie_tool._send_regular_request_with_json_instruction
        
        result = movie_tool.recommend_movies(test_request, model="openai/gpt-4o")
        
        # Восстанавливаем оригинальный метод
        movie_tool._send_structured_request = original_method
        
        if result["success"]:
            data = result["data"]
            print(f"✅ Fallback режим работает")
            print(f"📝 Статус: {data.get('status')}")
            print(f"💬 Сообщение: {data.get('message')}")
            return True
        else:
            print(f"❌ Ошибка fallback: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка fallback теста: {e}")
        return False


def main():
    """Основная функция тестирования"""
    
    print("🎬 Robust Movie Recommendation Test Suite")
    print("=" * 50)
    
    # Проверка переменных окружения
    required_vars = ["OPENROUTER_API_KEY", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return
    
    print("✅ Переменные окружения настроены")
    
    # Тест 1: Прямое подключение к БД
    db_works = test_database_direct()
    
    if not db_works:
        print("\n❌ База данных недоступна. Проверьте настройки.")
        return
    
    # Тест 2: Простой запрос к OpenRouter
    simple_works = test_simple_request()
    
    if not simple_works:
        print("\n⚠️ OpenRouter API недоступен, но БД работает")
        print("   Можете использовать Database Tools напрямую")
        return
    
    # Тест 3: Fallback режим
    fallback_works = test_fallback_mode()
    
    if fallback_works:
        print("\n✅ Fallback режим работает!")
    else:
        print("\n⚠️ Fallback режим не работает")
    
    # Тест 4: Разные модели
    working_model = test_with_different_models()
    
    if working_model:
        print(f"\n🎉 Система работает! Рекомендуемая модель: {working_model}")
    else:
        print("\n⚠️ Structured outputs не работают, но система может работать в fallback режиме")
    
    print("\n📋 Рекомендации:")
    print("1. Если structured outputs не работают, система автоматически переключится на fallback")
    print("2. Fallback режим использует текстовые инструкции для получения JSON")
    print("3. Все функции Database Tools работают независимо от OpenRouter")


if __name__ == "__main__":
    main()
