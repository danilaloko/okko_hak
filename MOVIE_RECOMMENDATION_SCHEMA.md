# JSON Schema для системы подбора фильмов

## Обзор

Система подбора фильмов использует OpenRouter Structured Outputs для возврата структурированных ответов в формате JSON Schema.

## Структура ответа

```json
{
  "status": "found",
  "message": "Нашел отличные комедии для вас!",
  "clarification_questions": [],
  "recommended_movie_ids": [123, 456, 789],
  "search_criteria": {
    "genres": ["Комедия"],
    "actors": ["Джим Керри"],
    "directors": [],
    "year_from": 2020,
    "year_to": 2023,
    "content_type": "Фильм"
  },
  "confidence": 0.85
}
```

## Поля ответа

### Обязательные поля

#### `status` (string)
Статус обработки запроса:
- `"need_more_info"` - нужна дополнительная информация
- `"searching"` - выполняется поиск
- `"found"` - фильмы найдены
- `"not_found"` - фильмы не найдены

#### `message` (string)
Текстовое сообщение для пользователя на русском языке

### Опциональные поля

#### `clarification_questions` (array of strings)
Уточняющие вопросы, если нужна дополнительная информация:
```json
[
  "Какой жанр вы предпочитаете?",
  "Есть ли любимые актеры?",
  "Какой период времени вас интересует?"
]
```

#### `recommended_movie_ids` (array of integers)
ID рекомендованных фильмов из базы данных:
```json
[123, 456, 789, 1011]
```

#### `search_criteria` (object)
Критерии поиска, которые использовались:

##### `genres` (array of strings)
Жанры для поиска:
```json
["Комедия", "Драма", "Боевик"]
```

##### `actors` (array of strings)
Актеры для поиска:
```json
["Леонардо ДиКаприо", "Том Хэнкс"]
```

##### `directors` (array of strings)
Режиссеры для поиска:
```json
["Кристофер Нолан", "Квентин Тарантино"]
```

##### `year_from` (integer)
Год выпуска "от":
```json
2020
```

##### `year_to` (integer)
Год выпуска "до":
```json
2023
```

##### `content_type` (string)
Тип контента:
- `"Фильм"`
- `"Сериал"`
- `"Многосерийный фильм"`

#### `confidence` (number)
Уверенность в рекомендации от 0 до 1:
```json
0.85
```

## Примеры ответов

### 1. Нужна дополнительная информация
```json
{
  "status": "need_more_info",
  "message": "Хорошо! Чтобы подобрать идеальный фильм, уточните:",
  "clarification_questions": [
    "Какой жанр вы предпочитаете?",
    "Есть ли любимые актеры или режиссеры?",
    "Какой период времени вас интересует?"
  ],
  "confidence": 0.0
}
```

### 2. Фильмы найдены
```json
{
  "status": "found",
  "message": "Отлично! Нашел несколько комедий с Джимом Керри. Рекомендую эти фильмы.",
  "recommended_movie_ids": [123, 456, 789],
  "search_criteria": {
    "genres": ["Комедия"],
    "actors": ["Джим Керри"],
    "content_type": "Фильм"
  },
  "confidence": 0.9
}
```

### 3. Фильмы не найдены
```json
{
  "status": "not_found",
  "message": "К сожалению, не нашел фильмы по вашим критериям. Попробуйте изменить параметры поиска.",
  "search_criteria": {
    "genres": ["Несуществующий жанр"],
    "year_from": 1900,
    "year_to": 1900
  },
  "confidence": 0.0
}
```

### 4. Выполняется поиск
```json
{
  "status": "searching",
  "message": "Ищу подходящие фильмы в базе данных...",
  "search_criteria": {
    "genres": ["Боевик"],
    "year_from": 2020,
    "year_to": 2023
  },
  "confidence": 0.0
}
```

## Валидация схемы

Схема использует следующие ограничения:

- `additionalProperties: false` - запрещены дополнительные поля
- `strict: true` - строгое соответствие схеме
- Обязательные поля: `status`, `message`
- Валидные значения для `status` и `content_type`
- Числовые ограничения для `confidence` (0-1)
- Целые числа для `year_from`, `year_to`, `recommended_movie_ids`

## Интеграция с OpenRouter

Схема передается в параметре `response_format`:

```json
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "movie_recommendation",
      "strict": true,
      "schema": {
        // ... полная схема
      }
    }
  }
}
```

## Обработка ошибок

При ошибках парсинга JSON возвращается:

```json
{
  "status": "error",
  "message": "Ошибка обработки ответа",
  "error": "JSONDecodeError: ..."
}
```

## Использование в коде

```python
# Получение структурированного ответа
result = movie_tool.recommend_movies("Хочу комедию")

if result["success"]:
    data = result["data"]
    
    # Проверка статуса
    if data["status"] == "found":
        movie_ids = data["recommended_movie_ids"]
        message = data["message"]
        confidence = data["confidence"]
        
        # Использование данных
        print(f"Найдено {len(movie_ids)} фильмов")
        print(f"Уверенность: {confidence * 100}%")
    
    elif data["status"] == "need_more_info":
        questions = data["clarification_questions"]
        # Задать уточняющие вопросы пользователю
```
