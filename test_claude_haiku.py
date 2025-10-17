"""
Тест для проверки работы с моделью Claude Haiku 4.5
"""

import os
import json
from dotenv import load_dotenv
import requests

# Загружаем переменные окружения
load_dotenv()


def test_claude_haiku_direct():
    """Прямой тест модели Claude Haiku через OpenRouter"""
    
    print("🧠 Тест модели Claude Haiku 4.5")
    print("=" * 40)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY не найден")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "anthropic/claude-haiku-4.5",
        "messages": [
            {
                "role": "system",
                "content": "Ты - помощник для подбора фильмов. Отвечай на русском языке кратко и по делу."
            },
            {
                "role": "user",
                "content": "Хочу посмотреть комедию. Что посоветуешь?"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    try:
        print("🔍 Отправляем запрос к Claude Haiku...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            
            print("✅ Успешный ответ от Claude Haiku:")
            print(f"💬 {ai_response}")
            
            # Проверяем, что ответ на русском и содержит рекомендации
            if any(word in ai_response.lower() for word in ['комедия', 'фильм', 'посмотреть', 'рекомендую']):
                print("🎉 Модель работает корректно!")
                return True
            else:
                print("⚠️ Ответ не содержит ожидаемых слов")
                return False
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_simple_chat_service():
    """Тест простого чат сервиса"""
    
    print("\n💬 Тест простого чат сервиса")
    print("=" * 40)
    
    try:
        # Проверяем, что сервис запущен
        health_response = requests.get("http://localhost:5004/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ Чат сервис не запущен")
            return False
        
        print("✅ Чат сервис доступен")
        
        # Отправляем тестовое сообщение
        test_data = {
            "user_id": "test_user",
            "message": "Хочу посмотреть комедию",
            "model": "anthropic/claude-haiku-4.5"
        }
        
        print("🔍 Отправляем тестовое сообщение...")
        response = requests.post(
            "http://localhost:5004/api/chat/message",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                ai_response = data.get('response', '')
                print("✅ Успешный ответ от чат сервиса:")
                print(f"💬 {ai_response}")
                print(f"🤖 Модель: {data.get('model')}")
                return True
            else:
                print(f"❌ Ошибка сервиса: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def main():
    """Основная функция"""
    
    print("🧠 Тест модели Claude Haiku 4.5")
    print("=" * 50)
    
    # Проверка переменных окружения
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY не найден")
        return
    
    print("✅ Переменные окружения настроены")
    
    # Тест 1: Прямой запрос к модели
    direct_success = test_claude_haiku_direct()
    
    # Тест 2: Через чат сервис
    service_success = test_simple_chat_service()
    
    print(f"\n📊 Результаты тестов:")
    print(f"  - Прямой запрос к Claude Haiku: {'✅' if direct_success else '❌'}")
    print(f"  - Через чат сервис: {'✅' if service_success else '❌'}")
    
    if direct_success and service_success:
        print(f"\n🎉 Модель Claude Haiku 4.5 работает отлично!")
        print(f"💡 Рекомендации:")
        print(f"   - Модель быстрая и надежная")
        print(f"   - Хорошо понимает русский язык")
        print(f"   - Подходит для чата с пользователями")
    elif direct_success:
        print(f"\n⚠️ Модель работает, но есть проблемы с сервисом")
    else:
        print(f"\n❌ Есть проблемы с моделью или API")


if __name__ == "__main__":
    main()
