"""
Тестовый скрипт для демонстрации работы Database Tools с OpenRouter
"""

import os
import json
from dotenv import load_dotenv
from openrouter_with_db_tools import OpenRouterWithDBTools

# Загружаем переменные окружения
load_dotenv()


def test_database_tools():
    """Тестирование Database Tools"""
    
    print("=== Тестирование Database Tools с OpenRouter ===\n")
    
    try:
        # Создание клиента
        client = OpenRouterWithDBTools()
        print("✓ Клиент OpenRouter с DB Tools создан успешно\n")
        
        # Тестовые вопросы
        test_questions = [
            "Покажи все таблицы в базе данных",
            "Какая версия PostgreSQL используется?",
            "Сколько таблиц в базе данных?",
            "Покажи информацию о схеме базы данных"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"--- Тест {i}: {question} ---")
            
            try:
                response = client.simple_db_query(question)
                print(f"Ответ: {response}")
                
            except Exception as e:
                print(f"Ошибка: {e}")
            
            print("-" * 60)
        
        print("\n=== Тестирование завершено ===")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        print("\nПроверьте:")
        print("1. Настроены ли переменные окружения (.env файл)")
        print("2. Доступна ли PostgreSQL база данных")
        print("3. Правильные ли данные для подключения к БД")


def test_direct_database_connection():
    """Тестирование прямого подключения к БД"""
    
    print("\n=== Тестирование прямого подключения к БД ===\n")
    
    try:
        from database_tool import DatabaseTool
        
        # Создание Database Tool
        db_tool = DatabaseTool()
        print("✓ Подключение к БД установлено успешно\n")
        
        # Тест получения списка таблиц
        print("--- Получение списка таблиц ---")
        tables_result = db_tool.get_available_tables()
        print(json.dumps(tables_result, ensure_ascii=False, indent=2))
        
        # Тест простого запроса
        print("\n--- Тест простого запроса ---")
        version_result = db_tool.execute_sql_query("SELECT version()")
        print(json.dumps(version_result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        print("\nПроверьте настройки БД в .env файле")


def check_environment():
    """Проверка переменных окружения"""
    
    print("=== Проверка переменных окружения ===\n")
    
    required_vars = [
        "OPENROUTER_API_KEY",
        "DB_HOST",
        "DB_PORT", 
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Скрываем пароли и ключи
            if "PASSWORD" in var or "KEY" in var:
                display_value = "*" * len(value)
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
        else:
            print(f"✗ {var}: НЕ НАЙДЕН")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        print("Создайте .env файл на основе env_example.txt")
        return False
    else:
        print("\n✓ Все необходимые переменные настроены")
        return True


if __name__ == "__main__":
    print("Database Tools Test Suite")
    print("=" * 50)
    
    # Проверяем переменные окружения
    if not check_environment():
        exit(1)
    
    # Тестируем прямое подключение к БД
    test_direct_database_connection()
    
    # Тестируем интеграцию с OpenRouter
    test_database_tools()
