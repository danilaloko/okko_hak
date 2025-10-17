"""
Специальный тест для модели Qwen3-VL-8B-Thinking
"""

import os
import json
from dotenv import load_dotenv
from movie_recommendation_tool import MovieRecommendationTool

# Загружаем переменные окружения
load_dotenv()


def test_qwen_model():
    """Тестирование модели Qwen3-VL-8B-Thinking"""
    
    print("🧠 Тестирование модели Qwen3-VL-8B-Thinking")
    print("=" * 50)
    
    try:
        # Создание системы с моделью Qwen
        movie_tool = MovieRecommendationTool()
        print("✅ Система создана с моделью Qwen")
        
        # Тестовые запросы для проверки thinking capabilities
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
                "request": "Хочу посмотреть что-то интересное на выходные",
                "description": "Очень неопределенный запрос"
            }
        ]
        
        for i, test_case in enumerate(test_requests, 1):
            print(f"\n--- Тест {i}: {test_case['description']} ---")
            print(f"Запрос: \"{test_case['request']}\"")
            
            try:
                result = movie_tool.recommend_movies(
                    test_case['request'], 
                    model="qwen/qwen3-vl-8b-thinking"
                )
                
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
                    
                    # Показываем полный JSON для анализа thinking процесса
                    print(f"\n📋 Полный JSON ответ:")
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    
                else:
                    print(f"❌ Ошибка: {result.get('error')}")
                    print(f"📝 Сообщение: {result.get('message')}")
                
            except Exception as e:
                print(f"❌ Исключение: {e}")
            
            print("-" * 60)
        
        print("\n🎉 Тестирование модели Qwen завершено!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


def test_qwen_thinking_capabilities():
    """Тестирование thinking capabilities модели Qwen"""
    
    print("\n🧠 Тестирование thinking capabilities")
    print("=" * 40)
    
    try:
        movie_tool = MovieRecommendationTool()
        
        # Сложный запрос для проверки reasoning
        complex_request = """
        Я хочу посмотреть фильм, но не знаю что выбрать. 
        Мне нравятся фильмы с хорошим сюжетом и интересными персонажами. 
        Не люблю ужасы и слишком жестокие фильмы. 
        Предпочитаю что-то современное, но не против и классики.
        Что бы ты посоветовал?
        """
        
        print(f"🔍 Сложный запрос: \"{complex_request.strip()}\"")
        
        result = movie_tool.recommend_movies(
            complex_request, 
            model="qwen/qwen3-vl-8b-thinking"
        )
        
        if result["success"]:
            data = result["data"]
            
            print(f"\n✅ Результат thinking анализа:")
            print(f"📝 Статус: {data.get('status')}")
            print(f"💬 Сообщение: {data.get('message')}")
            
            # Анализируем качество reasoning
            if data.get('clarification_questions'):
                print(f"\n🧠 Качество reasoning (уточняющие вопросы):")
                for i, question in enumerate(data['clarification_questions'], 1):
                    print(f"   {i}. {question}")
            
            if data.get('search_criteria'):
                criteria = data['search_criteria']
                print(f"\n🎯 Выведенные критерии:")
                if criteria.get('genres'):
                    print(f"   Жанры: {', '.join(criteria['genres'])}")
                if criteria.get('content_type'):
                    print(f"   Тип контента: {criteria['content_type']}")
            
            if data.get('confidence') is not None:
                confidence_percent = int(data['confidence'] * 100)
                print(f"\n🎯 Уверенность в анализе: {confidence_percent}%")
            
            print(f"\n📊 Количество итераций reasoning: {result.get('iterations')}")
            
        else:
            print(f"❌ Ошибка thinking: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Ошибка thinking теста: {e}")


def main():
    """Основная функция"""
    
    print("🧠 Qwen3-VL-8B-Thinking Test Suite")
    print("=" * 50)
    
    # Проверка переменных окружения
    required_vars = ["OPENROUTER_API_KEY", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return
    
    print("✅ Переменные окружения настроены")
    
    # Основное тестирование
    test_qwen_model()
    
    # Тестирование thinking capabilities
    test_qwen_thinking_capabilities()
    
    print("\n📋 Особенности модели Qwen3-VL-8B-Thinking:")
    print("1. 🧠 Thinking capabilities - модель может 'думать' перед ответом")
    print("2. 🎯 Лучше понимает сложные запросы")
    print("3. 🔍 Более качественный анализ пользовательских предпочтений")
    print("4. 📊 Высокая уверенность в рекомендациях")
    print("5. 🎬 Поддержка structured outputs")


if __name__ == "__main__":
    main()
