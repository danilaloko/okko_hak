"""
Быстрый тест системы подбора фильмов
"""

import os
import json
from dotenv import load_dotenv
from movie_recommendation_tool import MovieRecommendationTool

# Загружаем переменные окружения
load_dotenv()


def quick_test():
    """Быстрый тест системы"""
    
    print("🎬 Быстрый тест системы подбора фильмов")
    print("=" * 40)
    
    try:
        # Создание системы
        movie_tool = MovieRecommendationTool()
        print("✅ Система создана")
        
        # Простой тестовый запрос
        test_request = "Хочу посмотреть комедию"
        print(f"\n🔍 Тестовый запрос: \"{test_request}\"")
        
        # Выполнение запроса с моделью Qwen
        result = movie_tool.recommend_movies(test_request, model="qwen/qwen3-vl-8b-thinking")
        
        if result["success"]:
            data = result["data"]
            print(f"\n✅ Успешно!")
            print(f"📝 Статус: {data.get('status')}")
            print(f"💬 Сообщение: {data.get('message')}")
            
            if data.get('recommended_movie_ids'):
                print(f"🎯 Фильмы: {data['recommended_movie_ids']}")
            
            if data.get('clarification_questions'):
                print("❓ Вопросы:")
                for q in data['clarification_questions']:
                    print(f"   - {q}")
            
            print(f"\n📊 Итераций: {result.get('iterations')}")
            
        else:
            print(f"❌ Ошибка: {result.get('error')}")
            print(f"💬 Сообщение: {result.get('message')}")
        
        # Показываем полный JSON ответ
        print(f"\n📋 Полный ответ:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    quick_test()
