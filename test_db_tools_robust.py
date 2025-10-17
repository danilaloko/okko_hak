"""
Улучшенный тестовый скрипт с поддержкой разных моделей и retry логики
"""

import os
import json
from dotenv import load_dotenv
from openrouter_with_db_tools import OpenRouterWithDBTools

# Загружаем переменные окружения
load_dotenv()


def test_with_different_models():
    """Тестирование с разными моделями"""
    
    # Список моделей для тестирования
    models_to_try = [
        "openai/gpt-4o",
        "anthropic/claude-3-sonnet", 
        "google/gemini-2.0-flash-001",
        "meta-llama/llama-3.1-8b-instruct"
    ]
    
    test_question = "Покажи все таблицы в базе данных"
    
    print("=== Тестирование с разными моделями ===\n")
    
    for model in models_to_try:
        print(f"--- Тестирование модели: {model} ---")
        
        try:
            client = OpenRouterWithDBTools()
            response = client.simple_db_query(test_question, model=model)
            
            if "Ошибка" not in response:
                print(f"✅ Успех с моделью {model}")
                print(f"Ответ: {response[:200]}...")
                return model  # Возвращаем рабочую модель
            else:
                print(f"❌ Ошибка с моделью {model}: {response}")
                
        except Exception as e:
            print(f"❌ Исключение с моделью {model}: {e}")
        
        print("-" * 60)
    
    return None


def test_direct_database_only():
    """Тестирование только Database Tool без OpenRouter"""
    
    print("\n=== Тестирование только Database Tool ===\n")
    
    try:
        from database_tool import DatabaseTool
        
        db_tool = DatabaseTool()
        print("✅ Подключение к БД установлено")
        
        # Тест 1: Список таблиц
        print("\n--- Список таблиц ---")
        tables_result = db_tool.get_available_tables()
        if tables_result["success"]:
            print(f"✅ Найдено таблиц: {len(tables_result['data'])}")
            for table in tables_result["data"][:5]:  # Показываем первые 5
                print(f"  - {table['table_name']} ({table['table_type']})")
        else:
            print(f"❌ Ошибка: {tables_result['error']}")
        
        # Тест 2: Версия PostgreSQL
        print("\n--- Версия PostgreSQL ---")
        version_result = db_tool.execute_sql_query("SELECT version()")
        if version_result["success"]:
            print(f"✅ {version_result['data'][0]['version']}")
        else:
            print(f"❌ Ошибка: {version_result['error']}")
        
        # Тест 3: Информация о базе
        print("\n--- Информация о базе ---")
        db_info_result = db_tool.execute_sql_query("""
            SELECT 
                current_database() as database_name,
                current_user as current_user,
                inet_server_addr() as server_ip,
                inet_server_port() as server_port
        """)
        if db_info_result["success"]:
            info = db_info_result["data"][0]
            print(f"✅ База: {info['database_name']}, Пользователь: {info['current_user']}")
            print(f"   Сервер: {info['server_ip']}:{info['server_port']}")
        else:
            print(f"❌ Ошибка: {db_info_result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Критическая ошибка БД: {e}")
        return False


def test_manual_tool_calls():
    """Ручное тестирование tool calls"""
    
    print("\n=== Ручное тестирование Tool Calls ===\n")
    
    try:
        from database_tool import execute_database_query, list_database_tables
        
        # Тест 1: Список таблиц
        print("--- Tool: list_database_tables ---")
        result = list_database_tables()
        result_data = json.loads(result)
        if result_data["success"]:
            print(f"✅ Найдено таблиц: {len(result_data['data'])}")
        else:
            print(f"❌ Ошибка: {result_data['error']}")
        
        # Тест 2: SQL запрос
        print("\n--- Tool: execute_database_query ---")
        result = execute_database_query("SELECT current_timestamp as current_time")
        result_data = json.loads(result)
        if result_data["success"]:
            print(f"✅ Текущее время: {result_data['data'][0]['current_time']}")
        else:
            print(f"❌ Ошибка: {result_data['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка tool calls: {e}")
        return False


def main():
    """Основная функция тестирования"""
    
    print("🔧 Robust Database Tools Test Suite")
    print("=" * 50)
    
    # Проверка переменных окружения
    required_vars = ["OPENROUTER_API_KEY", "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return
    
    print("✅ Переменные окружения настроены")
    
    # Тест 1: Только Database Tool
    db_works = test_direct_database_only()
    
    if not db_works:
        print("\n❌ Database Tool не работает. Проверьте настройки БД.")
        return
    
    # Тест 2: Ручные tool calls
    tools_work = test_manual_tool_calls()
    
    if not tools_work:
        print("\n❌ Tool calls не работают.")
        return
    
    # Тест 3: OpenRouter с разными моделями
    working_model = test_with_different_models()
    
    if working_model:
        print(f"\n🎉 Система работает! Рекомендуемая модель: {working_model}")
    else:
        print("\n⚠️  OpenRouter API недоступен, но Database Tools работают")
        print("   Можете использовать Database Tools напрямую")


if __name__ == "__main__":
    main()
