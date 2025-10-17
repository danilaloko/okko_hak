"""
Пример использования OpenRouter клиента
"""

from openrouter_client import OpenRouterClient
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Основная функция с примерами использования"""
    
    try:
        # Создание клиента
        client = OpenRouterClient()
        
        print("=== Примеры использования OpenRouter ===\n")
        
        # 1. Простой запрос
        print("1. Простой запрос:")
        response = client.simple_request(
            "Привет! Расскажи коротко о себе.",
            model="openai/gpt-4o"
        )
        print(f"Ответ: {response}\n")
        
        # 2. Запрос с системным промптом
        print("2. Запрос с системным промптом:")
        response = client.simple_request(
            "Напиши короткое стихотворение о программировании",
            model="openai/gpt-4o",
            system_prompt="Ты - поэт, который пишет стихи о технологиях. Пиши коротко и креативно."
        )
        print(f"Стихотворение: {response}\n")
        
        # 3. Запрос с дополнительными параметрами
        print("3. Запрос с дополнительными параметрами:")
        response = client.simple_request(
            "Объясни квантовую физику простыми словами",
            model="openai/gpt-4o",
            temperature=0.3,  # Более детерминированный ответ
            max_tokens=200    # Ограничение длины ответа
        )
        print(f"Объяснение: {response}\n")
        
        # 4. Использование разных моделей
        print("4. Тестирование разных моделей:")
        models_to_test = [
            "openai/gpt-4o",
            "anthropic/claude-3-sonnet",
            "meta-llama/llama-3.1-8b-instruct"
        ]
        
        for model in models_to_test:
            try:
                print(f"Тестируем модель: {model}")
                response = client.simple_request(
                    "Скажи 'Привет!' на русском языке",
                    model=model,
                    max_tokens=50
                )
                print(f"Ответ от {model}: {response}")
            except Exception as e:
                print(f"Ошибка с моделью {model}: {e}")
            print()
        
        # 5. Получение списка доступных моделей
        print("5. Получение списка моделей:")
        try:
            models = client.get_available_models()
            print(f"Доступно моделей: {len(models)}")
            
            # Показываем первые 5 моделей
            print("Первые 5 моделей:")
            for i, model in enumerate(models[:5]):
                print(f"  {i+1}. {model.get('id', 'Unknown')} - {model.get('name', 'No name')}")
                
        except Exception as e:
            print(f"Ошибка при получении списка моделей: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка в main: {e}")
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
