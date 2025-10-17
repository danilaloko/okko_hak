"""
Простой микросервис чата с ИИ без сложных tools
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import os
from dotenv import load_dotenv
import requests
from celebrities_data import get_celebrity_by_id, get_all_celebrities, get_celebrity_system_prompt

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Конфигурация OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Глобальное состояние диалогов пользователей
user_dialogs = {}


def try_fallback_model(message, user_id, original_model, celebrity_id=None):
    """Попробовать fallback модели"""
    fallback_models = [
        "anthropic/claude-haiku-4.5",
        "openai/gpt-4o-mini",
        "qwen/qwen3-vl-8b-thinking"
    ]
    
    # Убираем оригинальную модель из списка fallback
    fallback_models = [m for m in fallback_models if m != original_model]
    
    for fallback_model in fallback_models:
        try:
            logger.info(f"Пробуем fallback модель: {fallback_model}")
            
            # Получаем историю диалога
            history = user_dialogs.get(user_id, [])
            
            # Формируем системный промпт в зависимости от выбранной знаменитости
            if celebrity_id:
                system_prompt = get_celebrity_system_prompt(celebrity_id)
                if not system_prompt:
                    system_prompt = """Ты - помощник для подбора фильмов. Твоя задача - помочь пользователю выбрать фильм для просмотра.

Правила:
- Отвечай на русском языке
- Будь дружелюбным и полезным
- Задавай уточняющие вопросы, если нужно
- Предлагай конкретные фильмы с объяснением
- Если не знаешь конкретный фильм, предложи жанр или тип

Примеры ответов:
- "Отлично! Какой жанр вас интересует? Комедия, драма, боевик?"
- "Рекомендую посмотреть 'Интерстеллар' - отличная фантастика с глубоким сюжетом"
- "Для вечернего просмотра подойдет 'Темный рыцарь' - классика жанра"""
            else:
                system_prompt = """Ты - помощник для подбора фильмов. Твоя задача - помочь пользователю выбрать фильм для просмотра.

Правила:
- Отвечай на русском языке
- Будь дружелюбным и полезным
- Задавай уточняющие вопросы, если нужно
- Предлагай конкретные фильмы с объяснением
- Если не знаешь конкретный фильм, предложи жанр или тип

Примеры ответов:
- "Отлично! Какой жанр вас интересует? Комедия, драма, боевик?"
- "Рекомендую посмотреть 'Интерстеллар' - отличная фантастика с глубоким сюжетом"
- "Для вечернего просмотра подойдет 'Темный рыцарь' - классика жанра"""
            
            # Формируем сообщения для OpenRouter
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
            
            # Добавляем историю диалога
            for entry in history[-5:]:  # Последние 5 сообщений
                messages.append({"role": "user", "content": entry["user_message"]})
                messages.append({"role": "assistant", "content": entry["assistant_response"]})
            
            # Добавляем текущее сообщение
            messages.append({"role": "user", "content": message})
            
            # Отправляем запрос к OpenRouter
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": fallback_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                ai_response = response_data["choices"][0]["message"]["content"]
                
                # Сохраняем в историю диалога
                if user_id not in user_dialogs:
                    user_dialogs[user_id] = []
                
                user_dialogs[user_id].append({
                    "user_message": message,
                    "assistant_response": ai_response,
                    "timestamp": "now"
                })
                
                # Ограничиваем историю до 10 сообщений
                if len(user_dialogs[user_id]) > 10:
                    user_dialogs[user_id] = user_dialogs[user_id][-10:]
                
                logger.info(f"Успешный fallback с моделью {fallback_model}")
                
                return jsonify({
                    "success": True,
                    "response": ai_response,
                    "model": fallback_model,
                    "user_id": user_id,
                    "fallback": True
                })
            else:
                logger.warning(f"Fallback модель {fallback_model} тоже недоступна: {response.status_code}")
                continue
                
        except Exception as e:
            logger.error(f"Ошибка с fallback моделью {fallback_model}: {e}")
            continue
    
    # Если все fallback модели не работают
    logger.error("Все модели недоступны")
    return jsonify({
        "success": False,
        "error": "Все модели недоступны",
        "response": "Извините, в данный момент сервис недоступен. Попробуйте позже."
    }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        "status": "healthy",
        "service": "simple_chat",
        "openrouter_available": bool(OPENROUTER_API_KEY)
    })


@app.route('/api/celebrities', methods=['GET'])
def get_celebrities():
    """Получить список всех знаменитостей"""
    try:
        celebrities = get_all_celebrities()
        return jsonify({
            "success": True,
            "celebrities": celebrities
        })
    except Exception as e:
        logger.error(f"Ошибка получения списка знаменитостей: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка получения знаменитостей: {str(e)}"
        }), 500


@app.route('/api/celebrities/<celebrity_id>', methods=['GET'])
def get_celebrity(celebrity_id):
    """Получить данные конкретной знаменитости"""
    try:
        celebrity = get_celebrity_by_id(celebrity_id)
        if celebrity:
            return jsonify({
                "success": True,
                "celebrity": celebrity
            })
        else:
            return jsonify({
                "success": False,
                "error": "Знаменитость не найдена"
            }), 404
    except Exception as e:
        logger.error(f"Ошибка получения знаменитости {celebrity_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка получения знаменитости: {str(e)}"
        }), 500


@app.route('/api/chat/message', methods=['POST'])
def chat_message():
    """Простой чат с ИИ"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        message = data.get('message', '')
        model = data.get('model', 'x-ai/grok-4-fast')
        celebrity_id = data.get('celebrity_id')
        
        if not message:
            return jsonify({
                "success": False,
                "error": "Сообщение не может быть пустым"
            }), 400
        
        if not OPENROUTER_API_KEY:
            return jsonify({
                "success": False,
                "error": "OpenRouter API ключ не настроен"
            }), 500
        
        logger.info(f"Получен запрос от пользователя {user_id} с знаменитостью {celebrity_id}: {message}")
        
        # Получаем историю диалога
        history = user_dialogs.get(user_id, [])
        
        # Формируем системный промпт в зависимости от выбранной знаменитости
        if celebrity_id:
            system_prompt = get_celebrity_system_prompt(celebrity_id)
            if not system_prompt:
                logger.warning(f"Не найден промпт для знаменитости {celebrity_id}, используем стандартный")
                system_prompt = """Ты - помощник для подбора фильмов. Твоя задача - помочь пользователю выбрать фильм для просмотра.

Правила:
- Отвечай на русском языке
- Будь дружелюбным и полезным
- Задавай уточняющие вопросы, если нужно
- Предлагай конкретные фильмы с объяснением
- Если не знаешь конкретный фильм, предложи жанр или тип

Примеры ответов:
- "Отлично! Какой жанр вас интересует? Комедия, драма, боевик?"
- "Рекомендую посмотреть 'Интерстеллар' - отличная фантастика с глубоким сюжетом"
- "Для вечернего просмотра подойдет 'Темный рыцарь' - классика жанра"""
        else:
            system_prompt = """Ты - помощник для подбора фильмов. Твоя задача - помочь пользователю выбрать фильм для просмотра.

Правила:
- Отвечай на русском языке
- Будь дружелюбным и полезным
- Задавай уточняющие вопросы, если нужно
- Предлагай конкретные фильмы с объяснением
- Если не знаешь конкретный фильм, предложи жанр или тип

Примеры ответов:
- "Отлично! Какой жанр вас интересует? Комедия, драма, боевик?"
- "Рекомендую посмотреть 'Интерстеллар' - отличная фантастика с глубоким сюжетом"
- "Для вечернего просмотра подойдет 'Темный рыцарь' - классика жанра"""
        
        # Формируем сообщения для OpenRouter
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # Добавляем историю диалога
        for entry in history[-5:]:  # Последние 5 сообщений
            messages.append({"role": "user", "content": entry["user_message"]})
            messages.append({"role": "assistant", "content": entry["assistant_response"]})
        
        # Добавляем текущее сообщение
        messages.append({"role": "user", "content": message})
        
        # Отправляем запрос к OpenRouter
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            ai_response = response_data["choices"][0]["message"]["content"]
            
            # Сохраняем в историю диалога
            if user_id not in user_dialogs:
                user_dialogs[user_id] = []
            
            user_dialogs[user_id].append({
                "user_message": message,
                "assistant_response": ai_response,
                "timestamp": "now"
            })
            
            # Ограничиваем историю до 10 сообщений
            if len(user_dialogs[user_id]) > 10:
                user_dialogs[user_id] = user_dialogs[user_id][-10:]
            
            logger.info(f"Успешный ответ для пользователя {user_id}")
            
            return jsonify({
                "success": True,
                "response": ai_response,
                "model": model,
                "user_id": user_id
            })
        elif response.status_code == 403:
            # Модель недоступна, пробуем fallback
            logger.warning(f"Модель {model} недоступна (403), пробуем fallback")
            return try_fallback_model(message, user_id, model, celebrity_id)
        else:
            logger.error(f"Ошибка OpenRouter API: {response.status_code}")
            return jsonify({
                "success": False,
                "error": f"Ошибка API: {response.status_code}",
                "response": "Извините, произошла ошибка. Попробуйте еще раз."
            }), 500
            
    except requests.exceptions.Timeout:
        logger.error("Таймаут запроса к OpenRouter")
        return jsonify({
            "success": False,
            "error": "Таймаут запроса",
            "response": "Извините, запрос занял слишком много времени. Попробуйте еще раз."
        }), 500
    except Exception as e:
        logger.error(f"Ошибка в chat_message: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Внутренняя ошибка: {str(e)}",
            "response": "Извините, произошла ошибка. Попробуйте еще раз."
        }), 500


@app.route('/api/chat/history/<user_id>', methods=['GET'])
def get_chat_history(user_id):
    """Получить историю диалога пользователя"""
    try:
        history = user_dialogs.get(user_id, [])
        return jsonify({
            "success": True,
            "user_id": user_id,
            "history": history
        })
    except Exception as e:
        logger.error(f"Ошибка получения истории для пользователя {user_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка получения истории: {str(e)}"
        }), 500


@app.route('/api/chat/clear-history/<user_id>', methods=['POST'])
def clear_chat_history(user_id):
    """Очистить историю диалога пользователя"""
    try:
        if user_id in user_dialogs:
            del user_dialogs[user_id]
        
        return jsonify({
            "success": True,
            "message": f"История диалога для пользователя {user_id} очищена"
        })
    except Exception as e:
        logger.error(f"Ошибка очистки истории для пользователя {user_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка очистки истории: {str(e)}"
        }), 500


@app.route('/api/chat/models', methods=['GET'])
def get_available_models():
    """Получить список доступных моделей"""
    try:
        models = [
            "x-ai/grok-4-fast",
            "anthropic/claude-haiku-4.5",
            "openai/gpt-4o-mini",
            "qwen/qwen3-vl-8b-thinking",
            "google/gemini-2.0-flash-001"
        ]
        
        return jsonify({
            "success": True,
            "models": models,
            "default_model": "x-ai/grok-4-fast"
        })
    except Exception as e:
        logger.error(f"Ошибка получения списка моделей: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка получения моделей: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint не найден"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Внутренняя ошибка сервера"
    }), 500


if __name__ == '__main__':
    port = int(os.getenv('SIMPLE_CHAT_PORT', 5004))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Запуск простого чат сервиса на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
