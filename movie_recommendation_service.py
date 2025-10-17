"""
Микросервис для подбора фильмов с использованием OpenRouter и Database Tools
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import os
from dotenv import load_dotenv
from movie_recommendation_tool import MovieRecommendationTool

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Инициализация системы подбора фильмов
try:
    movie_tool = MovieRecommendationTool()
    logger.info("Система подбора фильмов успешно инициализирована")
except Exception as e:
    logger.error(f"Ошибка инициализации системы подбора фильмов: {e}")
    movie_tool = None

# Глобальное состояние диалогов пользователей
user_dialogs = {}


@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервиса"""
    return jsonify({
        "status": "healthy",
        "service": "movie_recommendation",
        "movie_tool_available": movie_tool is not None
    })


@app.route('/api/movie-recommendation/chat', methods=['POST'])
def movie_chat():
    """Основной endpoint для диалога с системой подбора фильмов"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        message = data.get('message', '')
        model = data.get('model', 'qwen/qwen3-vl-8b-thinking')
        
        if not message:
            return jsonify({
                "success": False,
                "error": "Сообщение не может быть пустым"
            }), 400
        
        if not movie_tool:
            return jsonify({
                "success": False,
                "error": "Система подбора фильмов недоступна"
            }), 500
        
        logger.info(f"Получен запрос от пользователя {user_id}: {message}")
        
        # Выполняем подбор фильмов
        result = movie_tool.recommend_movies(message, model=model)
        
        if result["success"]:
            data = result["data"]
            
            # Сохраняем историю диалога
            if user_id not in user_dialogs:
                user_dialogs[user_id] = []
            
            user_dialogs[user_id].append({
                "user_message": message,
                "assistant_response": data,
                "timestamp": "now"
            })
            
            # Формируем ответ
            response = {
                "success": True,
                "status": data.get('status'),
                "message": data.get('message'),
                "clarification_questions": data.get('clarification_questions', []),
                "recommended_movie_ids": data.get('recommended_movie_ids', []),
                "search_criteria": data.get('search_criteria', {}),
                "confidence": data.get('confidence', 0.0),
                "iterations": result.get('iterations', 0)
            }
            
            logger.info(f"Успешный ответ для пользователя {user_id}: статус {data.get('status')}")
            return jsonify(response)
        else:
            logger.error(f"Ошибка подбора фильмов для пользователя {user_id}: {result.get('error')}")
            return jsonify({
                "success": False,
                "error": result.get('error'),
                "message": result.get('message', 'Ошибка при подборе фильмов')
            }), 500
            
    except Exception as e:
        logger.error(f"Ошибка в movie_chat: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


@app.route('/api/movie-recommendation/history/<user_id>', methods=['GET'])
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


@app.route('/api/movie-recommendation/clear-history/<user_id>', methods=['POST'])
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


@app.route('/api/movie-recommendation/models', methods=['GET'])
def get_available_models():
    """Получить список доступных моделей"""
    try:
        models = [
            "qwen/qwen3-vl-8b-thinking",
            "anthropic/claude-haiku-4.5",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.0-flash-001",
            "meta-llama/llama-3.1-8b-instruct"
        ]
        
        return jsonify({
            "success": True,
            "models": models,
            "default_model": "qwen/qwen3-vl-8b-thinking"
        })
    except Exception as e:
        logger.error(f"Ошибка получения списка моделей: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка получения моделей: {str(e)}"
        }), 500


@app.route('/api/movie-recommendation/database/query', methods=['POST'])
def direct_database_query():
    """Прямой запрос к базе данных (для отладки)"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                "success": False,
                "error": "SQL запрос не может быть пустым"
            }), 400
        
        if not movie_tool:
            return jsonify({
                "success": False,
                "error": "Система подбора фильмов недоступна"
            }), 500
        
        # Выполняем прямой запрос к БД
        from database_tool import DatabaseTool
        db_tool = DatabaseTool()
        result = db_tool.execute_sql_query(query)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка прямого запроса к БД: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка запроса к БД: {str(e)}"
        }), 500


@app.route('/api/movie-recommendation/database/tables', methods=['GET'])
def get_database_tables():
    """Получить список таблиц в базе данных"""
    try:
        if not movie_tool:
            return jsonify({
                "success": False,
                "error": "Система подбора фильмов недоступна"
            }), 500
        
        from database_tool import DatabaseTool
        db_tool = DatabaseTool()
        result = db_tool.get_available_tables()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка получения списка таблиц: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка получения таблиц: {str(e)}"
        }), 500


@app.route('/api/movie-recommendation/database/schema/<table_name>', methods=['GET'])
def get_table_schema(table_name):
    """Получить схему таблицы"""
    try:
        if not movie_tool:
            return jsonify({
                "success": False,
                "error": "Система подбора фильмов недоступна"
            }), 500
        
        from database_tool import DatabaseTool
        db_tool = DatabaseTool()
        result = db_tool.get_table_schema(table_name)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка получения схемы таблицы {table_name}: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Ошибка получения схемы: {str(e)}"
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
    port = int(os.getenv('MOVIE_RECOMMENDATION_PORT', 5003))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Запуск микросервиса подбора фильмов на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
