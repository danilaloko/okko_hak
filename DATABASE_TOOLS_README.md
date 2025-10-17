# Database Tools для OpenRouter

Система позволяет нейронным сетям выполнять SQL запросы к PostgreSQL базе данных через OpenRouter Tool Calling.

## Возможности

- ✅ Выполнение SQL запросов (SELECT, INSERT, UPDATE, DELETE)
- ✅ Получение схемы таблиц
- ✅ Список доступных таблиц
- ✅ Безопасность (защита от опасных операций)
- ✅ Интеграция с OpenRouter API
- ✅ Автоматическое выполнение tool calls

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` на основе `env_example.txt`:
```bash
cp env_example.txt .env
```

3. Настройте переменные окружения в `.env`:
```env
# OpenRouter API
OPENROUTER_API_KEY=your_api_key_here

# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
```

## Использование

### Простое использование

```python
from openrouter_with_db_tools import OpenRouterWithDBTools

# Создание клиента
client = OpenRouterWithDBTools()

# Запрос к базе данных через нейронную сеть
response = client.simple_db_query("Покажи все таблицы в базе данных")
print(response)
```

### Расширенное использование

```python
from openrouter_with_db_tools import OpenRouterWithDBTools

client = OpenRouterWithDBTools()

# Настройка сообщений
messages = [
    {
        "role": "system", 
        "content": "Ты помощник для работы с базой данных фильмов"
    },
    {
        "role": "user", 
        "content": "Найди все фильмы с рейтингом выше 8.0"
    }
]

# Отправка запроса с поддержкой tool calling
response = client.chat_with_db_tools(messages, model="openai/gpt-4o")
print(response["content"])
```

### Прямое использование Database Tool

```python
from database_tool import DatabaseTool

# Создание tool
db_tool = DatabaseTool()

# Выполнение SQL запроса
result = db_tool.execute_sql_query("SELECT * FROM movies LIMIT 5")
print(result)

# Получение схемы таблицы
schema = db_tool.get_table_schema("movies")
print(schema)

# Список таблиц
tables = db_tool.get_available_tables()
print(tables)
```

## Доступные Tools

### 1. execute_database_query
Выполняет SQL запросы к базе данных.

**Параметры:**
- `query` (string, обязательный): SQL запрос
- `params` (object, опциональный): Параметры запроса

**Пример:**
```sql
SELECT * FROM movies WHERE rating > 8.0
```

### 2. get_database_schema
Получает структуру указанной таблицы.

**Параметры:**
- `table_name` (string, обязательный): Название таблицы

### 3. list_database_tables
Получает список всех доступных таблиц.

## Безопасность

Система включает защиту от опасных операций:

- ✅ Разрешены только: SELECT, INSERT, UPDATE, DELETE
- ❌ Запрещены: DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE
- ❌ Запрещены комментарии в SQL
- ✅ Параметризованные запросы для защиты от SQL инъекций

## Тестирование

Запустите тестовый скрипт:

```bash
python test_db_tools.py
```

Скрипт проверит:
- Настройки переменных окружения
- Подключение к базе данных
- Работу с OpenRouter API
- Выполнение различных типов запросов

## Примеры запросов

### Для нейронной сети:

1. **"Покажи все таблицы в базе данных"**
2. **"Какая структура у таблицы movies?"**
3. **"Сколько фильмов с рейтингом выше 8.0?"**
4. **"Найди все фильмы 2023 года"**
5. **"Покажи топ-10 фильмов по рейтингу"**

### Прямые SQL запросы:

```sql
-- Получение информации о таблицах
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Поиск фильмов
SELECT title, rating FROM movies WHERE rating > 8.0 ORDER BY rating DESC;

-- Статистика
SELECT COUNT(*) as total_movies FROM movies;
```

## Структура файлов

- `database_tool.py` - Основной модуль для работы с БД
- `openrouter_with_db_tools.py` - Интеграция с OpenRouter
- `test_db_tools.py` - Тестовый скрипт
- `env_example.txt` - Пример настроек
- `requirements.txt` - Зависимости

## Обработка ошибок

Система возвращает структурированные ответы:

```json
{
  "success": true,
  "data": [...],
  "row_count": 10,
  "columns": ["id", "title", "rating"]
}
```

При ошибках:
```json
{
  "success": false,
  "error": "Описание ошибки",
  "error_type": "SQL_ERROR"
}
```

## Логирование

Все операции логируются с уровнем INFO. Для отладки можно изменить уровень:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Ограничения

- Максимум 5 итераций tool calling по умолчанию
- Таймаут 30 секунд для запросов
- Только PostgreSQL базы данных
- Защита от опасных SQL операций

## Интеграция с существующими проектами

Для интеграции с вашим Okkonator проектом:

1. Добавьте Database Tools в существующий OpenRouter клиент
2. Настройте подключение к вашей БД фильмов
3. Используйте для анализа данных и рекомендаций

```python
# В вашем okkonator_service.py
from openrouter_with_db_tools import OpenRouterWithDBTools

client = OpenRouterWithDBTools()

# Анализ предпочтений пользователя
response = client.simple_db_query(
    "Проанализируй предпочтения пользователя по жанрам фильмов"
)
```
