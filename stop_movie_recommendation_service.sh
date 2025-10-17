#!/bin/bash

# Скрипт остановки микросервиса подбора фильмов

echo "🛑 Остановка микросервиса подбора фильмов..."

# Проверяем наличие PID файла
if [ -f "movie_recommendation_service.pid" ]; then
    PID=$(cat movie_recommendation_service.pid)
    
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
    rm movie_recommendation_service.pid
    echo "🗑️  PID файл удален"
else
    echo "⚠️  PID файл не найден, ищем процесс по имени..."
    
    # Ищем процесс по имени
    PIDS=$(pgrep -f "movie_recommendation_service.py")
    
    if [ -n "$PIDS" ]; then
        echo "🔍 Найдены процессы: $PIDS"
        echo "⏹️  Останавливаем процессы..."
        
        for pid in $PIDS; do
            kill $pid
        done
        
        sleep 3
        
        # Проверяем, остановились ли процессы
        REMAINING_PIDS=$(pgrep -f "movie_recommendation_service.py")
        if [ -n "$REMAINING_PIDS" ]; then
            echo "⚠️  Некоторые процессы не остановились, принудительно завершаем..."
            for pid in $REMAINING_PIDS; do
                kill -9 $pid
            done
        fi
        
        echo "✅ Процессы остановлены"
    else
        echo "ℹ️  Процессы микросервиса не найдены"
    fi
fi

# Проверяем, что порт 5003 свободен
if lsof -Pi :5003 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Порт 5003 все еще занят"
    echo "🔍 Процессы на порту 5003:"
    lsof -Pi :5003 -sTCP:LISTEN
else
    echo "✅ Порт 5003 свободен"
fi

echo ""
echo "🎬 Микросервис подбора фильмов остановлен"
echo "📋 Логи сохранены в: logs/movie_recommendation_service.log"
