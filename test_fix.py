"""
Тест для проверки исправления ошибки обработки ответа
"""

import os
import json
from dotenv import load_dotenv
from movie_recommendation_tool import MovieRecommendationTool

# Загружаем переменные окружения
load_dotenv()


def test_simple_request():
    """Простой тест запроса"""
    
    print("🔧 Тест исправления ошибки обработки ответа")
    print("=" * 50)
    
    try:
        movie_tool = MovieRecommendationTool()
        
        # Простой тестовый запрос
        test_request = "Хочу посмотреть комедию"
        print(f"🔍 Тестовый запрос: \"{test_request}\"")
        
        result = movie_tool.recommend_movies(test_request, model="qwen/qwen3-vl-8b-thinking")
        
        print(f"\n📊 Результат:")
        print(f"✅ Успех: {result['success']}")
        
        if result["success"]:
            data = result["data"]
            print(f"📝 Статус: {data.get('status')}")
            print(f"💬 Сообщение: {data.get('message')}")
            
            if data.get('recommended_movie_ids'):
                print(f"🎯 Фильмы: {data['recommended_movie_ids']}")
            
            if data.get('clarification_questions'):
                print(f"❓ Вопросы: {len(data['clarification_questions'])}")
            
            if data.get('confidence') is not None:
                confidence_percent = int(data['confidence'] * 100)
                print(f"🎯 Уверенность: {confidence_percent}%")
            
            print(f"🔄 Итераций: {result.get('iterations')}")
            
        else:
            print(f"❌ Ошибка: {result.get('error')}")
            print(f"💬 Сообщение: {result.get('message')}")
            
            # Показываем дополнительную информацию об ошибке
            if 'raw_content' in result:
                print(f"📄 Сырой ответ: {result['raw_content'][:200]}...")
            
            if 'cleaned_content' in result:
                print(f"🧹 Очищенный ответ: {result['cleaned_content'][:200]}...")
        
        # Показываем полный результат
        print(f"\n📋 Полный результат:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return result["success"]
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False


def test_fallback_mode():
    """Тест fallback режима"""
    
    print("\n🔄 Тест fallback режима")
    print("=" * 30)
    
    try:
        movie_tool = MovieRecommendationTool()
        
        # Принудительно используем fallback режим
        test_request = "Покажи фильмы с Леонардо ДиКаприо"
        
        # Модифицируем метод для принудительного fallback
        original_method = movie_tool._send_structured_request
        movie_tool._send_structured_request = movie_tool._send_regular_request_with_json_instruction
        
        result = movie_tool.recommend_movies(test_request, model="qwen/qwen3-vl-8b-thinking")
        
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
            if 'raw_content' in result:
                print(f"📄 Сырой ответ: {result['raw_content'][:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка fallback теста: {e}")
        return False


def main():
    """Основная функция"""
    
    print("🔧 Тест исправления ошибки обработки ответа")
    print("=" * 50)
    
    # Проверка переменных окружения
    required_vars = ["OPENROUTER_API_KEY", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return
    
    print("✅ Переменные окружения настроены")
    
    # Тест 1: Обычный запрос
    success1 = test_simple_request()
    
    # Тест 2: Fallback режим
    success2 = test_fallback_mode()
    
    print(f"\n📊 Результаты тестов:")
    print(f"  - Обычный запрос: {'✅' if success1 else '❌'}")
    print(f"  - Fallback режим: {'✅' if success2 else '❌'}")
    
    if success1 or success2:
        print(f"\n🎉 Исправления работают!")
    else:
        print(f"\n⚠️  Нужны дополнительные исправления")


if __name__ == "__main__":
    main()
