#!/bin/bash

# Скрипт запуска микросервиса подбора фильмов

echo "🎬 Запуск микросервиса подбора фильмов..."

# Проверяем, что виртуальное окружение активировано
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Виртуальное окружение не активировано. Активируем..."
    source env/bin/activate
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте .env файл на основе env_example.txt"
    exit 1
fi

# Проверяем, что порт 5003 свободен
if lsof -Pi :5003 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Порт 5003 уже занят. Останавливаем существующий процесс..."
    pkill -f "movie_recommendation_service.py"
    sleep 2
fi

# Запускаем микросервис в фоновом режиме
echo "🚀 Запускаем микросервис на порту 5003..."
nohup python movie_recommendation_service.py > logs/movie_recommendation_service.log 2>&1 &

# Сохраняем PID процесса
echo $! > movie_recommendation_service.pid

# Ждем немного и проверяем, что сервис запустился
sleep 3

if [ -f "movie_recommendation_service.pid" ]; then
    PID=$(cat movie_recommendation_service.pid)
    if ps -p $PID > /dev/null; then
        echo "✅ Микросервис подбора фильмов успешно запущен!"
        echo "📊 PID: $PID"
        echo "🌐 URL: http://localhost:5003"
        echo "📋 Логи: logs/movie_recommendation_service.log"
        echo ""
        echo "🔍 Проверка здоровья сервиса..."
        curl -s http://localhost:5003/health | python -m json.tool
    else
        echo "❌ Ошибка запуска микросервиса"
        echo "📋 Проверьте логи: logs/movie_recommendation_service.log"
        exit 1
    fi
else
    echo "❌ Не удалось создать PID файл"
    exit 1
fi

echo ""
echo "🎯 Доступные endpoints:"
echo "  - POST /api/movie-recommendation/chat - основной чат"
echo "  - GET  /api/movie-recommendation/history/<user_id> - история диалога"
echo "  - POST /api/movie-recommendation/clear-history/<user_id> - очистка истории"
echo "  - GET  /api/movie-recommendation/models - список моделей"
echo "  - GET  /health - проверка здоровья"
echo ""
echo "🛑 Для остановки используйте: ./stop_movie_recommendation_service.sh"
