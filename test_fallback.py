"""
Простой тест fallback режима для системы подбора фильмов
"""

import os
import json
from dotenv import load_dotenv
from movie_recommendation_tool import MovieRecommendationTool

# Загружаем переменные окружения
load_dotenv()


def test_fallback_mode():
    """Тест fallback режима (без structured outputs)"""
    
    print("🔄 Тест Fallback режима")
    print("=" * 30)
    
    try:
        movie_tool = MovieRecommendationTool()
        
        # Принудительно используем fallback режим
        test_request = "Хочу посмотреть комедию"
        
        print(f"🔍 Тестовый запрос: \"{test_request}\"")
        
        # Модифицируем метод для принудительного fallback
        original_method = movie_tool._send_structured_request
        movie_tool._send_structured_request = movie_tool._send_regular_request_with_json_instruction
        
        result = movie_tool.recommend_movies(test_request, model="qwen/qwen3-vl-8b-thinking")
        
        # Восстанавливаем оригинальный метод
        movie_tool._send_structured_request = original_method
        
        if result["success"]:
            data = result["data"]
            print(f"\n✅ Fallback режим работает!")
            print(f"📝 Статус: {data.get('status')}")
            print(f"💬 Сообщение: {data.get('message')}")
            
            if data.get('recommended_movie_ids'):
                print(f"🎯 Фильмы: {data['recommended_movie_ids']}")
            
            if data.get('clarification_questions'):
                print("❓ Уточняющие вопросы:")
                for question in data['clarification_questions']:
                    print(f"   - {question}")
            
            if data.get('search_criteria'):
                criteria = data['search_criteria']
                print("🔍 Критерии поиска:")
                if criteria.get('genres'):
                    print(f"   Жанры: {', '.join(criteria['genres'])}")
                if criteria.get('content_type'):
                    print(f"   Тип: {criteria['content_type']}")
            
            if data.get('confidence') is not None:
                confidence_percent = int(data['confidence'] * 100)
                print(f"🎯 Уверенность: {confidence_percent}%")
            
            print(f"\n🔄 Итераций: {result.get('iterations')}")
            
            # Показываем полный JSON
            print(f"\n📋 Полный JSON ответ:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            
            return True
        else:
            print(f"❌ Ошибка fallback: {result.get('error')}")
            if result.get('message'):
                print(f"💬 Сообщение: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка fallback теста: {e}")
        return False


def test_database_only():
    """Тест только базы данных"""
    
    print("\n🗄️ Тест только базы данных")
    print("=" * 30)
    
    try:
        from database_tool import DatabaseTool
        
        db_tool = DatabaseTool()
        
        # Поиск комедий
        print("--- Поиск комедий ---")
        comedy_result = db_tool.execute_sql_query("""
            SELECT t.title_id, t.serial_name, t.content_type, t.release_date
            FROM title t
            JOIN title_genre tg ON t.title_id = tg.title_id
            JOIN genre g ON tg.genre_id = g.genre_id
            WHERE g.name ILIKE '%комедия%' 
            AND t.content_type = 'Фильм'
            LIMIT 5
        """)
        
        if comedy_result["success"]:
            print(f"✅ Найдено комедий: {len(comedy_result['data'])}")
            for movie in comedy_result["data"]:
                print(f"   - {movie['serial_name']} (ID: {movie['title_id']}, {movie['release_date']})")
        else:
            print(f"❌ Ошибка поиска комедий: {comedy_result['error']}")
        
        # Поиск жанров
        print("\n--- Доступные жанры ---")
        genres_result = db_tool.execute_sql_query("""
            SELECT name FROM genre 
            WHERE name ILIKE '%комедия%' OR name ILIKE '%драма%' OR name ILIKE '%боевик%'
            LIMIT 10
        """)
        
        if genres_result["success"]:
            print(f"✅ Найдено жанров: {len(genres_result['data'])}")
            for genre in genres_result["data"]:
                print(f"   - {genre['name']}")
        else:
            print(f"❌ Ошибка поиска жанров: {genres_result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False


def main():
    """Основная функция"""
    
    print("🎬 Fallback Test Suite")
    print("=" * 30)
    
    # Проверка переменных окружения
    required_vars = ["OPENROUTER_API_KEY", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return
    
    print("✅ Переменные окружения настроены")
    
    # Тест 1: Только база данных
    db_works = test_database_only()
    
    if not db_works:
        print("\n❌ База данных недоступна")
        return
    
    # Тест 2: Fallback режим
    fallback_works = test_fallback_mode()
    
    if fallback_works:
        print("\n🎉 Fallback режим работает отлично!")
        print("\n💡 Рекомендации:")
        print("1. Система автоматически переключится на fallback при ошибках structured outputs")
        print("2. Fallback режим использует текстовые инструкции для получения JSON")
        print("3. Все функции работают, просто без гарантии structured outputs")
    else:
        print("\n⚠️ Fallback режим не работает")
        print("Проверьте подключение к OpenRouter API")


if __name__ == "__main__":
    main()
