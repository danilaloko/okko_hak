"""
Система запросов к нейросетям через OpenRouter API
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import requests

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


class OpenRouterClient:
    """Клиент для работы с OpenRouter API"""
    
    def __init__(self, config: Optional[OpenRouterConfig] = None):
        """
        Инициализация клиента OpenRouter
        
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
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-4o",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Отправка запроса к модели через OpenRouter
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "текст"}]
            model: Название модели (например, "openai/gpt-4o", "anthropic/claude-3-sonnet")
            temperature: Температура генерации (0.0 - 2.0)
            max_tokens: Максимальное количество токенов в ответе
            stream: Включить потоковую передачу
            **kwargs: Дополнительные параметры для API
            
        Returns:
            Ответ от API в формате словаря
            
        Raises:
            Exception: При ошибке запроса
        """
        try:
            logger.info(f"Отправка запроса к модели {model}")
            
            # Подготовка данных запроса
            data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": stream,
                **kwargs
            }
            
            if max_tokens is not None:
                data["max_tokens"] = max_tokens
            
            # Отправка запроса
            url = f"{self.config.base_url}/chat/completions"
            response = requests.post(
                url,
                headers=self.headers,
                json=data,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            
            if stream:
                return self._handle_streaming_response(response)
            else:
                return self._handle_regular_response(response.json())
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HTTP при запросе к OpenRouter: {str(e)}")
            raise Exception(f"Ошибка HTTP: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка при запросе к OpenRouter: {str(e)}")
            raise
    
    def _handle_regular_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка обычного (не потокового) ответа"""
        return {
            "content": response_data["choices"][0]["message"]["content"],
            "model": response_data.get("model", "unknown"),
            "usage": response_data.get("usage", {}),
            "finish_reason": response_data["choices"][0].get("finish_reason", "unknown")
        }
    
    def _handle_streaming_response(self, response) -> Dict[str, Any]:
        """Обработка потокового ответа"""
        content = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Убираем 'data: '
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                content += delta['content']
                    except json.JSONDecodeError:
                        continue
        
        return {
            "content": content,
            "model": "unknown",
            "stream": True
        }
    
    def simple_request(
        self,
        prompt: str,
        model: str = "openai/gpt-4o",
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Упрощенный метод для отправки запроса
        
        Args:
            prompt: Текст запроса
            model: Название модели
            system_prompt: Системный промпт (опционально)
            **kwargs: Дополнительные параметры
            
        Returns:
            Текст ответа от модели
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat_completion(messages, model, **kwargs)
        return response["content"]
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Получение списка доступных моделей
        
        Returns:
            Список доступных моделей
        """
        try:
            response = requests.get(
                f"{self.config.base_url}/models",
                headers=self.headers,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей: {str(e)}")
            raise


# Пример использования
if __name__ == "__main__":
    try:
        # Создание клиента
        client = OpenRouterClient()
        
        # Простой запрос
        response = client.simple_request(
            "Привет! Как дела?",
            model="openai/gpt-4o"
        )
        print(f"Ответ: {response}")
        
        # Запрос с системным промптом
        response = client.simple_request(
            "Расскажи анекдот",
            model="openai/gpt-4o",
            system_prompt="Ты - веселый комедиант. Отвечай коротко и с юмором."
        )
        print(f"Анекдот: {response}")
        
        # Получение списка моделей
        models = client.get_available_models()
        print(f"Доступно моделей: {len(models)}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
