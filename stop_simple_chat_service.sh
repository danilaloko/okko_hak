#!/bin/bash

# Скрипт остановки простого чат сервиса

echo "🛑 Остановка простого чат сервиса..."

# Проверяем наличие PID файла
if [ -f "simple_chat_service.pid" ]; then
    PID=$(cat simple_chat_service.pid)
    
    if ps -p $PID > /dev/null; then
        echo "🔍 Найден процесс с PID: $PID"
        echo "⏹️  Останавливаем процесс..."
        
        # Пытаемся остановить процесс gracefully
        kill $PID
        
        # Ждем 5 секунд
        sleep 5
        
        # Проверяем, остановился ли процесс
        if ps -p $PID > /dev/null; then
            echo "⚠️  Процесс не остановился gracefully, принудительно завершаем..."
            kill -9 $PID
            sleep 2
        fi
        
        # Финальная проверка
        if ps -p $PID > /dev/null; then
            echo "❌ Не удалось остановить процесс"
            exit 1
        else
            echo "✅ Процесс успешно остановлен"
        fi
    else
        echo "⚠️  Процесс с PID $PID не найден"
    fi
    
    # Удаляем PID файл
    rm simple_chat_service.pid
    echo "🗑️  PID файл удален"
else
    echo "⚠️  PID файл не найден, ищем процесс по имени..."
    
    # Ищем процесс по имени
    PIDS=$(pgrep -f "simple_chat_service.py")
    
    if [ -n "$PIDS" ]; then
        echo "🔍 Найдены процессы: $PIDS"
        echo "⏹️  Останавливаем процессы..."
        
        for pid in $PIDS; do
            kill $pid
        done
        
        sleep 3
        
        # Проверяем, остановились ли процессы
        REMAINING_PIDS=$(pgrep -f "simple_chat_service.py")
        if [ -n "$REMAINING_PIDS" ]; then
            echo "⚠️  Некоторые процессы не остановились, принудительно завершаем..."
            for pid in $REMAINING_PIDS; do
                kill -9 $pid
            done
        fi
        
        echo "✅ Процессы остановлены"
    else
        echo "ℹ️  Процессы сервиса не найдены"
    fi
fi

# Проверяем, что порт 5004 свободен
if lsof -Pi :5004 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Порт 5004 все еще занят"
    echo "🔍 Процессы на порту 5004:"
    lsof -Pi :5004 -sTCP:LISTEN
else
    echo "✅ Порт 5004 свободен"
fi

echo ""
echo "💬 Простой чат сервис остановлен"
echo "📋 Логи сохранены в: logs/simple_chat_service.log"
