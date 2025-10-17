"""
Tool для выполнения SQL запросов к PostgreSQL базе данных
Интеграция с OpenRouter Tool Calling
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Конфигурация для подключения к PostgreSQL"""
    host: str
    port: int
    database: str
    username: str
    password: str
    schema: Optional[str] = None


class DatabaseTool:
    """Tool для выполнения SQL запросов к PostgreSQL"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Инициализация Database Tool
        
        Args:
            config: Конфигурация БД. Если не указана, загружается из .env
        """
        if config is None:
            config = self._load_config_from_env()
        
        self.config = config
        self.engine = None
        self._connect()
    
    def _load_config_from_env(self) -> DatabaseConfig:
        """Загрузка конфигурации из переменных окружения"""
        required_vars = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        
        return DatabaseConfig(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME"),
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            schema=os.getenv("DB_SCHEMA")
        )
    
    def _connect(self):
        """Установка соединения с базой данных"""
        try:
            connection_string = (
                f"postgresql://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
            
            self.engine = create_engine(connection_string, echo=False)
            
            # Тестируем соединение
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Успешное подключение к PostgreSQL")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {str(e)}")
            raise
    
    def execute_sql_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнение SQL запроса
        
        Args:
            query: SQL запрос
            params: Параметры для запроса (опционально)
            
        Returns:
            Результат выполнения запроса
        """
        try:
            logger.info(f"Выполнение SQL запроса: {query[:100]}...")
            
            # Проверка на опасные операции
            self._validate_query(query)
            
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                # Если это SELECT запрос, возвращаем данные
                if query.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    # Преобразуем в список словарей
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, column in enumerate(columns):
                            value = row[i]
                            # Преобразуем datetime и другие типы в строки
                            if hasattr(value, 'isoformat'):
                                value = value.isoformat()
                            row_dict[column] = value
                        data.append(row_dict)
                    
                    return {
                        "success": True,
                        "data": data,
                        "row_count": len(data),
                        "columns": list(columns)
                    }
                else:
                    # Для INSERT, UPDATE, DELETE возвращаем количество затронутых строк
                    conn.commit()
                    return {
                        "success": True,
                        "message": "Запрос выполнен успешно",
                        "row_count": result.rowcount
                    }
                    
        except SQLAlchemyError as e:
            logger.error(f"Ошибка SQL: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка SQL: {str(e)}",
                "error_type": "SQL_ERROR"
            }
        except Exception as e:
            logger.error(f"Общая ошибка: {str(e)}")
            return {
                "success": False,
                "error": f"Общая ошибка: {str(e)}",
                "error_type": "GENERAL_ERROR"
            }
    
    def _validate_query(self, query: str):
        """
        Валидация SQL запроса на предмет опасных операций
        
        Args:
            query: SQL запрос для проверки
            
        Raises:
            ValueError: Если запрос содержит опасные операции
        """
        query_upper = query.upper().strip()
        
        # Разрешенные операции
        allowed_operations = ['SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE']
        
        # Проверяем, что запрос начинается с разрешенной операции
        if not any(query_upper.startswith(op) for op in allowed_operations):
            raise ValueError("Разрешены только SELECT, INSERT, UPDATE, DELETE операции")
        
        # Запрещенные операции
        dangerous_operations = [
            'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE',
            'EXEC', 'EXECUTE', 'CALL', '--', '/*', '*/'
        ]
        
        for dangerous in dangerous_operations:
            if dangerous in query_upper:
                raise ValueError(f"Запрещенная операция: {dangerous}")
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Получение схемы таблицы
        
        Args:
            table_name: Название таблицы
            
        Returns:
            Схема таблицы
        """
        try:
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
            
            result = self.execute_sql_query(query, {"table_name": table_name})
            
            if result["success"]:
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": result["data"]
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Ошибка получения схемы таблицы: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка получения схемы: {str(e)}"
            }
    
    def get_available_tables(self) -> Dict[str, Any]:
        """
        Получение списка доступных таблиц
        
        Returns:
            Список таблиц
        """
        try:
            query = """
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
            
            return self.execute_sql_query(query)
            
        except Exception as e:
            logger.error(f"Ошибка получения списка таблиц: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка получения таблиц: {str(e)}"
            }


# Функция для использования в OpenRouter Tool Calling
def execute_database_query(query: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Функция для вызова из OpenRouter Tool Calling
    
    Args:
        query: SQL запрос
        params: Параметры запроса
        
    Returns:
        JSON строка с результатом
    """
    try:
        db_tool = DatabaseTool()
        result = db_tool.execute_sql_query(query, params)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Ошибка инициализации: {str(e)}",
            "error_type": "INIT_ERROR"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


def get_database_schema(table_name: str) -> str:
    """
    Функция для получения схемы таблицы через OpenRouter Tool Calling
    
    Args:
        table_name: Название таблицы
        
    Returns:
        JSON строка с схемой таблицы
    """
    try:
        db_tool = DatabaseTool()
        result = db_tool.get_table_schema(table_name)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Ошибка инициализации: {str(e)}",
            "error_type": "INIT_ERROR"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


def list_database_tables() -> str:
    """
    Функция для получения списка таблиц через OpenRouter Tool Calling
    
    Returns:
        JSON строка со списком таблиц
    """
    try:
        db_tool = DatabaseTool()
        result = db_tool.get_available_tables()
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Ошибка инициализации: {str(e)}",
            "error_type": "INIT_ERROR"
        }
        return json.dumps(error_result, ensure_ascii=False, indent=2)


# Определение tools для OpenRouter
DATABASE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_database_query",
            "description": "Выполнение SQL запроса к PostgreSQL базе данных. Поддерживает SELECT, INSERT, UPDATE, DELETE операции.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL запрос для выполнения. Поддерживаются SELECT, INSERT, UPDATE, DELETE операции."
                    },
                    "params": {
                        "type": "object",
                        "description": "Параметры для SQL запроса (опционально). Ключи - названия параметров, значения - их значения.",
                        "additionalProperties": True
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_database_schema",
            "description": "Получение схемы (структуры) указанной таблицы в базе данных",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Название таблицы, схему которой нужно получить"
                    }
                },
                "required": ["table_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_database_tables",
            "description": "Получение списка всех доступных таблиц в базе данных",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


# Пример использования
if __name__ == "__main__":
    try:
        # Создание Database Tool
        db_tool = DatabaseTool()
        
        # Получение списка таблиц
        print("=== Список таблиц ===")
        tables_result = db_tool.get_available_tables()
        print(json.dumps(tables_result, ensure_ascii=False, indent=2))
        
        # Пример SELECT запроса
        print("\n=== Пример SELECT запроса ===")
        select_result = db_tool.execute_sql_query("SELECT version()")
        print(json.dumps(select_result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Ошибка: {e}")
