"""
Система подбора фильмов с использованием OpenRouter Structured Outputs
"""

import os
import json
import logging
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


class MovieRecommendationTool:
    """Система подбора фильмов с Structured Outputs"""
    
    def __init__(self, config: Optional[OpenRouterConfig] = None):
        """
        Инициализация системы подбора фильмов
        
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
    
    def recommend_movies(
        self,
        user_request: str,
        model: str = "qwen/qwen3-vl-8b-thinking",
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Подбор фильмов на основе запроса пользователя
        
        Args:
            user_request: Запрос пользователя
            model: Модель для использования
            max_iterations: Максимальное количество итераций
            
        Returns:
            Структурированный ответ с рекомендациями
        """
        try:
            logger.info(f"Начинаем подбор фильмов для запроса: {user_request}")
            
            # Системный промпт для подбора фильмов
            system_prompt = """Ты - помощник для подбора фильма

ИНСТРУКЦИИ:
1. Проанализируй запрос от пользователя
2. Определи, достаточно ли информации дано. Если нет, то задай уточняющие вопросы
3. Определи какие tools надо использовать
4. Используй выбранные tools и получи информацию от них
5. Если ты готов подобрать фильмы для пользователя - верни их ids (в строгом формате)
6. Так же напиши текстовое сообщение, которое увидит пользователь

ПИШИ НА РУССКОМ
ТВОЯ ЗАДАЧА - ПОДБОР ФИЛЬМА И ВСЕ
ТЫ ДОЛЖЕН БЫТЬ УВЕРЕННЫМ В ВЫБОРЕ, ЗАДАВАЙ УТОЧНЯЮЩИЕ ВОПРОСЫ
ПИШИ КОРОТКО И ЛЕГКО, БУКВАЛЬНО ПАРУ ПРЕДЛОЖЕНИЙ
ОБЯЗАТЕЛЬНО ОТВЕТНОЕ СООБЩЕНИЕ!

ДОСТУПНЫЕ TOOLS:
- execute_database_query: для поиска фильмов в базе данных
- get_database_schema: для получения структуры таблиц
- list_database_tables: для получения списка таблиц

СХЕМА БАЗЫ ДАННЫХ:
- title: основная таблица с фильмами (title_id, serial_name, content_type, age_rating, release_date, description)
- genre: жанры фильмов
- actor: актеры
- director_item: режиссеры
- title_genre, title_actor, title_director_item: связи между фильмами и жанрами/актерами/режиссерами"""

            # Настройка сообщений
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ]
            
            # JSON Schema для структурированного ответа
            response_schema = {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["need_more_info", "searching", "found", "not_found"],
                        "description": "Статус обработки запроса"
                    },
                    "message": {
                        "type": "string",
                        "description": "Текстовое сообщение для пользователя"
                    },
                    "clarification_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Уточняющие вопросы, если нужна дополнительная информация"
                    },
                    "recommended_movie_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "ID рекомендованных фильмов"
                    },
                    "search_criteria": {
                        "type": "object",
                        "properties": {
                            "genres": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Жанры для поиска"
                            },
                            "actors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Актеры для поиска"
                            },
                            "directors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Режиссеры для поиска"
                            },
                            "year_from": {
                                "type": "integer",
                                "description": "Год выпуска от"
                            },
                            "year_to": {
                                "type": "integer",
                                "description": "Год выпуска до"
                            },
                            "content_type": {
                                "type": "string",
                                "enum": ["Фильм", "Сериал", "Многосерийный фильм"],
                                "description": "Тип контента"
                            }
                        },
                        "description": "Критерии поиска фильмов"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Уверенность в рекомендации (0-1)"
                    }
                },
                "required": ["status", "message"],
                "additionalProperties": False
            }
            
            # Выполняем чат с tool calling
            conversation_messages = messages.copy()
            
            for iteration in range(max_iterations):
                logger.info(f"Итерация {iteration + 1}/{max_iterations}")
                
                # Отправляем запрос с tools
                response = self._send_request_with_tools(
                    conversation_messages,
                    model,
                    tools=DATABASE_TOOLS
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
                    # Нет tool calls, получаем финальный структурированный ответ
                    logger.info("Получен финальный ответ, запрашиваем структурированный формат")
                    
                    # Добавляем запрос на структурированный ответ
                    conversation_messages.append({
                        "role": "assistant",
                        "content": response.get("content", "")
                    })
                    
                    conversation_messages.append({
                        "role": "user",
                        "content": "Теперь верни ответ в структурированном JSON формате согласно схеме."
                    })
                    
                    # Запрашиваем структурированный ответ
                    structured_response = self._send_structured_request(
                        conversation_messages,
                        model,
                        response_schema
                    )
                    
                    return {
                        "success": True,
                        "data": structured_response,
                        "iterations": iteration + 1,
                        "raw_conversation": conversation_messages
                    }
            
            # Если достигли максимального количества итераций
            logger.warning(f"Достигнуто максимальное количество итераций: {max_iterations}")
            return {
                "success": False,
                "error": "MAX_ITERATIONS_REACHED",
                "message": "Превышено максимальное количество итераций"
            }
            
        except Exception as e:
            logger.error(f"Ошибка в подборе фильмов: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Ошибка при подборе фильмов: {str(e)}"
            }
    
    def _send_request_with_tools(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Отправка запроса с tools к OpenRouter"""
        
        data = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "temperature": temperature
        }
        
        url = f"{self.config.base_url}/chat/completions"
        response = requests.post(
            url,
            headers=self.headers,
            json=data,
            timeout=self.config.timeout
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        choice = response_data["choices"][0]
        message = choice["message"]
        
        result = {
            "content": message.get("content"),
            "finish_reason": choice.get("finish_reason")
        }
        
        if message.get("tool_calls"):
            result["tool_calls"] = message["tool_calls"]
        
        return result
    
    def _send_structured_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Отправка запроса с structured outputs"""
        
        # Проверяем, поддерживает ли модель structured outputs
        models_with_structured_outputs = [
            "openai/gpt-4o",
            "openai/gpt-4o-mini", 
            "openai/gpt-4-turbo",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "qwen/qwen3-vl-8b-thinking"
        ]
        
        if model not in models_with_structured_outputs:
            logger.warning(f"Модель {model} может не поддерживать structured outputs, используем обычный запрос")
            return self._send_regular_request_with_json_instruction(messages, model, temperature)
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "movie_recommendation",
                    "strict": True,
                    "schema": response_schema
                }
            }
        }
        
        url = f"{self.config.base_url}/chat/completions"
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=data,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Парсим JSON ответ
            content = response_data["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                return {
                    "status": "error",
                    "message": "Ошибка обработки ответа",
                    "error": str(e)
                }
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                logger.warning(f"400 ошибка с structured outputs, пробуем обычный запрос: {e}")
                return self._send_regular_request_with_json_instruction(messages, model, temperature)
            else:
                raise
    
    def _send_regular_request_with_json_instruction(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Отправка обычного запроса с инструкцией вернуть JSON"""
        
        # Добавляем инструкцию по JSON формату
        json_instruction = """Верни ответ в следующем JSON формате:
{
  "status": "found|need_more_info|searching|not_found",
  "message": "текст сообщения на русском",
  "clarification_questions": ["вопрос1", "вопрос2"],
  "recommended_movie_ids": [123, 456],
  "search_criteria": {
    "genres": ["жанр1"],
    "actors": ["актер1"],
    "directors": ["режиссер1"],
    "year_from": 2020,
    "year_to": 2023,
    "content_type": "Фильм|Сериал|Многосерийный фильм"
  },
  "confidence": 0.85
}

Отвечай ТОЛЬКО валидным JSON, без дополнительного текста."""
        
        # Добавляем инструкцию к последнему сообщению пользователя
        messages_with_instruction = messages.copy()
        if messages_with_instruction and messages_with_instruction[-1]["role"] == "user":
            messages_with_instruction[-1]["content"] += f"\n\n{json_instruction}"
        else:
            messages_with_instruction.append({"role": "user", "content": json_instruction})
        
        data = {
            "model": model,
            "messages": messages_with_instruction,
            "temperature": temperature
        }
        
        url = f"{self.config.base_url}/chat/completions"
        response = requests.post(
            url,
            headers=self.headers,
            json=data,
            timeout=self.config.timeout
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        # Парсим JSON ответ
        content = response_data["choices"][0]["message"]["content"]
        
        # Очищаем ответ от возможных markdown блоков
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.error(f"Содержимое ответа: {content}")
            return {
                "status": "error",
                "message": "Ошибка обработки ответа",
                "error": str(e),
                "raw_content": content
            }
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """Выполнение tool call"""
        try:
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            
            logger.info(f"Выполнение tool: {function_name} с аргументами: {arguments}")
            
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


# Пример использования
if __name__ == "__main__":
    try:
        # Создание системы подбора фильмов
        movie_tool = MovieRecommendationTool()
        
        # Тестовые запросы
        test_requests = [
            "Хочу посмотреть комедию",
            "Покажи фильмы с Леонардо ДиКаприо",
            "Нужен хороший боевик 2020-2023 года",
            "Рекомендуй что-то романтическое"
        ]
        
        for request in test_requests:
            print(f"\n=== Запрос: {request} ===")
            result = movie_tool.recommend_movies(request)
            
            if result["success"]:
                data = result["data"]
                print(f"Статус: {data.get('status')}")
                print(f"Сообщение: {data.get('message')}")
                if data.get('recommended_movie_ids'):
                    print(f"Рекомендованные ID: {data['recommended_movie_ids']}")
                if data.get('clarification_questions'):
                    print(f"Уточняющие вопросы: {data['clarification_questions']}")
            else:
                print(f"Ошибка: {result.get('error')}")
            
            print("-" * 60)
        
    except Exception as e:
        print(f"Ошибка: {e}")
