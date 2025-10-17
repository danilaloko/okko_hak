"""
OpenRouter клиент с интеграцией Database Tools
Позволяет нейронной сети выполнять SQL запросы к PostgreSQL
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import requests

# Импортируем наши database tools
from database_tool import (
    execute_database_query,
    get_database_schema,
    list_database_tables,
    DATABASE_TOOLS
)

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OpenRouterConfig:
    """Конфигурация для OpenRouter API"""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    site_url: Optional[str] = None
    site_name: Optional[str] = None
    timeout: int = 30


class OpenRouterWithDBTools:
    """OpenRouter клиент с поддержкой Database Tools"""
    
    def __init__(self, config: Optional[OpenRouterConfig] = None):
        """
        Инициализация клиента OpenRouter с Database Tools
        
        Args:
            config: Конфигурация OpenRouter. Если не указана, загружается из .env
        """
        if config is None:
            config = self._load_config_from_env()
        
        self.config = config
        
        # Дополнительные заголовки для OpenRouter
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        if config.site_url:
            self.headers["HTTP-Referer"] = config.site_url
        if config.site_name:
            self.headers["X-Title"] = config.site_name
        
        # Маппинг функций для tool calling
        self.tool_functions = {
            "execute_database_query": execute_database_query,
            "get_database_schema": get_database_schema,
            "list_database_tables": list_database_tables
        }
    
    def _load_config_from_env(self) -> OpenRouterConfig:
        """Загрузка конфигурации из переменных окружения"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY не найден в переменных окружения")
        
        return OpenRouterConfig(
            api_key=api_key,
            site_url=os.getenv("OPENROUTER_SITE_URL"),
            site_name=os.getenv("OPENROUTER_SITE_NAME"),
            timeout=int(os.getenv("OPENROUTER_TIMEOUT", "30"))
        )
    
    def chat_with_db_tools(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Чат с поддержкой Database Tools
        
        Args:
            messages: Список сообщений
            model: Модель для использования
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
            max_iterations: Максимальное количество итераций tool calling
            
        Returns:
            Финальный ответ от модели
        """
        try:
            logger.info(f"Начинаем чат с моделью {model}")
            
            # Копируем сообщения для работы
            conversation_messages = messages.copy()
            
            for iteration in range(max_iterations):
                logger.info(f"Итерация {iteration + 1}/{max_iterations}")
                
                # Отправляем запрос с tools
                response = self._send_request_with_tools(
                    conversation_messages,
                    model,
                    temperature,
                    max_tokens
                )
                
                # Проверяем, есть ли tool calls
                if response.get("tool_calls"):
                    logger.info(f"Получено {len(response['tool_calls'])} tool calls")
                    
                    # Добавляем ответ ассистента в конверсацию
                    conversation_messages.append({
                        "role": "assistant",
                        "content": response.get("content"),
                        "tool_calls": response["tool_calls"]
                    })
                    
                    # Выполняем tool calls
                    for tool_call in response["tool_calls"]:
                        tool_result = self._execute_tool_call(tool_call)
                        
                        # Добавляем результат tool call в конверсацию
                        conversation_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": tool_result
                        })
                    
                    # Продолжаем итерацию
                    continue
                else:
                    # Нет tool calls, возвращаем финальный ответ
                    logger.info("Получен финальный ответ без tool calls")
                    return {
                        "content": response.get("content", ""),
                        "model": model,
                        "iterations": iteration + 1,
                        "success": True
                    }
            
            # Если достигли максимального количества итераций
            logger.warning(f"Достигнуто максимальное количество итераций: {max_iterations}")
            return {
                "content": "Достигнуто максимальное количество итераций. Попробуйте упростить запрос.",
                "model": model,
                "iterations": max_iterations,
                "success": False,
                "error": "MAX_ITERATIONS_REACHED"
            }
            
        except Exception as e:
            logger.error(f"Ошибка в чате с DB tools: {str(e)}")
            return {
                "content": f"Ошибка: {str(e)}",
                "model": model,
                "success": False,
                "error": str(e)
            }
    
    def _send_request_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Отправка запроса с tools к OpenRouter с retry логикой"""
        
        # Подготовка данных запроса
        data = {
            "model": model,
            "messages": messages,
            "tools": DATABASE_TOOLS,
            "temperature": temperature
        }
        
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        # Отправка запроса с retry
        url = f"{self.config.base_url}/chat/completions"
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=self.config.timeout
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Извлекаем нужные данные из ответа
                choice = response_data["choices"][0]
                message = choice["message"]
                
                result = {
                    "content": message.get("content"),
                    "finish_reason": choice.get("finish_reason")
                }
                
                # Если есть tool calls, добавляем их
                if message.get("tool_calls"):
                    result["tool_calls"] = message["tool_calls"]
                
                return result
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 502 and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Экспоненциальная задержка
                    logger.warning(f"502 ошибка, повтор через {wait_time} сек (попытка {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Ошибка запроса, повтор через {wait_time} сек (попытка {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """Выполнение tool call"""
        try:
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            
            logger.info(f"Выполнение tool: {function_name} с аргументами: {arguments}")
            
            # Получаем функцию из маппинга
            if function_name in self.tool_functions:
                function = self.tool_functions[function_name]
                result = function(**arguments)
                logger.info(f"Tool {function_name} выполнен успешно")
                return result
            else:
                error_msg = f"Неизвестная функция: {function_name}"
                logger.error(error_msg)
                return json.dumps({
                    "success": False,
                    "error": error_msg,
                    "error_type": "UNKNOWN_FUNCTION"
                }, ensure_ascii=False)
                
        except Exception as e:
            error_msg = f"Ошибка выполнения tool: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "success": False,
                "error": error_msg,
                "error_type": "TOOL_EXECUTION_ERROR"
            }, ensure_ascii=False)
    
    def simple_db_query(
        self,
        user_question: str,
        model: str = "openai/gpt-4o",
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Упрощенный метод для запроса к базе данных через нейронную сеть
        
        Args:
            user_question: Вопрос пользователя
            model: Модель для использования
            system_prompt: Системный промпт (опционально)
            
        Returns:
            Ответ от нейронной сети с результатами из БД
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            # Стандартный системный промпт для работы с БД
            messages.append({
                "role": "system",
                "content": """Ты - помощник для работы с базой данных PostgreSQL. 
                У тебя есть доступ к следующим инструментам:
                - execute_database_query: для выполнения SQL запросов
                - get_database_schema: для получения структуры таблиц
                - list_database_tables: для получения списка таблиц
                
                Используй эти инструменты для ответа на вопросы пользователя о данных в базе.
                Всегда объясняй результаты понятным языком."""
            })
        
        messages.append({"role": "user", "content": user_question})
        
        response = self.chat_with_db_tools(messages, model)
        return response.get("content", "Ошибка получения ответа")


# Пример использования
if __name__ == "__main__":
    try:
        # Создание клиента с DB tools
        client = OpenRouterWithDBTools()
        
        # Примеры запросов
        examples = [
            "Покажи все таблицы в базе данных",
            "Какая структура у таблицы users?",
            "Сколько записей в таблице movies?",
            "Найди все фильмы с рейтингом выше 8.0"
        ]
        
        for example in examples:
            print(f"\n=== Вопрос: {example} ===")
            response = client.simple_db_query(example)
            print(f"Ответ: {response}")
            print("-" * 50)
        
    except Exception as e:
        print(f"Ошибка: {e}")
