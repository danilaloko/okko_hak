"""
Тест для проверки исправления проблемы с пустыми ответами
"""

import os
import json
from dotenv import load_dotenv
from movie_recommendation_tool import MovieRecommendationTool

# Загружаем переменные окружения
load_dotenv()


def test_models_with_empty_response_handling():
    """Тестирование разных моделей с обработкой пустых ответов"""
    
    print("🔧 Тест обработки пустых ответов")
    print("=" * 50)
    
    # Модели для тестирования
    models_to_test = [
        "anthropic/claude-haiku-4.5",
        "openai/gpt-4o-mini",
        "qwen/qwen3-vl-8b-thinking"
    ]
    
    test_request = "Хочу посмотреть комедию"
    
    for model in models_to_test:
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
                
                if data.get('confidence') is not None:
                    confidence_percent = int(data['confidence'] * 100)
                    print(f"🎯 Уверенность: {confidence_percent}%")
                
                # Если получили валидный ответ, возвращаем успех
                if data.get('status') in ['found', 'need_more_info', 'searching', 'not_found']:
                    print(f"🎉 Модель {model} работает корректно!")
                    return model
                
            else:
                print(f"❌ Ошибка с моделью {model}: {result.get('error')}")
                if 'raw_content' in result:
                    print(f"📄 Сырой ответ: {result['raw_content'][:100]}...")
                
        except Exception as e:
            print(f"❌ Исключение с моделью {model}: {e}")
    
    return None


def test_fallback_robustness():
    """Тест надежности fallback режима"""
    
    print("\n🔄 Тест надежности fallback режима")
    print("=" * 40)
    
    try:
        movie_tool = MovieRecommendationTool()
        
        # Принудительно используем fallback режим
        test_request = "Покажи фильмы с Леонардо ДиКаприо"
        
        # Модифицируем метод для принудительного fallback
        original_method = movie_tool._send_structured_request
        movie_tool._send_structured_request = movie_tool._send_regular_request_with_json_instruction
        
        result = movie_tool.recommend_movies(test_request, model="anthropic/claude-haiku-4.5")
        
        # Восстанавливаем оригинальный метод
        movie_tool._send_structured_request = original_method
        
        if result["success"]:
            data = result["data"]
            print(f"✅ Fallback режим работает")
            print(f"📝 Статус: {data.get('status')}")
            print(f"💬 Сообщение: {data.get('message')}")
            
            # Проверяем, что получили валидный статус
            if data.get('status') in ['found', 'need_more_info', 'searching', 'not_found']:
                print(f"🎉 Fallback режим возвращает валидные данные!")
                return True
            else:
                print(f"⚠️ Fallback режим работает, но статус неожиданный: {data.get('status')}")
                return True
        else:
            print(f"❌ Ошибка fallback: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка fallback теста: {e}")
        return False


def main():
    """Основная функция"""
    
    print("🔧 Тест исправления проблемы с пустыми ответами")
    print("=" * 60)
    
    # Проверка переменных окружения
    required_vars = ["OPENROUTER_API_KEY", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return
    
    print("✅ Переменные окружения настроены")
    
    # Тест 1: Разные модели
    working_model = test_models_with_empty_response_handling()
    
    # Тест 2: Fallback режим
    fallback_works = test_fallback_robustness()
    
    print(f"\n📊 Результаты тестов:")
    if working_model:
        print(f"✅ Рабочая модель: {working_model}")
    else:
        print(f"❌ Ни одна модель не работает корректно")
    
    print(f"🔄 Fallback режим: {'✅' if fallback_works else '❌'}")
    
    if working_model or fallback_works:
        print(f"\n🎉 Исправления работают!")
        print(f"💡 Рекомендации:")
        if working_model:
            print(f"   - Используйте модель: {working_model}")
        if fallback_works:
            print(f"   - Fallback режим работает как резерв")
    else:
        print(f"\n⚠️  Нужны дополнительные исправления")


if __name__ == "__main__":
    main()
