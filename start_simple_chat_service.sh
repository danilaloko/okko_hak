#!/bin/bash

# Скрипт запуска простого чат сервиса

echo "💬 Запуск простого чат сервиса..."

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

# Проверяем, что порт 5004 свободен
if lsof -Pi :5004 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Порт 5004 уже занят. Останавливаем существующий процесс..."
    pkill -f "simple_chat_service.py"
    sleep 2
fi

# Запускаем микросервис в фоновом режиме
echo "🚀 Запускаем простой чат сервис на порту 5004..."
nohup python simple_chat_service.py > logs/simple_chat_service.log 2>&1 &

# Сохраняем PID процесса
echo $! > simple_chat_service.pid

# Ждем немного и проверяем, что сервис запустился
sleep 3

if [ -f "simple_chat_service.pid" ]; then
    PID=$(cat simple_chat_service.pid)
    if ps -p $PID > /dev/null; then
        echo "✅ Простой чат сервис успешно запущен!"
        echo "📊 PID: $PID"
        echo "🌐 URL: http://localhost:5004"
        echo "📋 Логи: logs/simple_chat_service.log"
        echo ""
        echo "🔍 Проверка здоровья сервиса..."
        curl -s http://localhost:5004/health | python -m json.tool
    else
        echo "❌ Ошибка запуска сервиса"
        echo "📋 Проверьте логи: logs/simple_chat_service.log"
        exit 1
    fi
else
    echo "❌ Не удалось создать PID файл"
    exit 1
fi

echo ""
echo "🎯 Доступные endpoints:"
echo "  - POST /api/chat/message - отправка сообщения"
echo "  - GET  /api/chat/history/<user_id> - история диалога"
echo "  - POST /api/chat/clear-history/<user_id> - очистка истории"
echo "  - GET  /api/chat/models - список моделей"
echo "  - GET  /health - проверка здоровья"
echo ""
echo "🛑 Для остановки используйте: ./stop_simple_chat_service.sh"
