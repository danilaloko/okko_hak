#!/bin/bash

# Скрипт для запуска всех микросервисов

echo "🚀 Запуск всех микросервисов Okko Hak..."

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

# Создаем папку для логов
mkdir -p logs

echo ""
echo "1️⃣  Запуск микросервиса Окконатора..."
./start_okkonator_service.sh

echo ""
echo "2️⃣  Запуск микросервиса Swipe..."
./start_swipe_service.sh

echo ""
echo "3️⃣  Запуск микросервиса подбора фильмов..."
./start_movie_recommendation_service.sh

echo ""
echo "4️⃣  Запуск основного приложения..."
echo "🌐 Основное приложение будет доступно на http://localhost:5000"

# Проверяем статус всех сервисов
echo ""
echo "🔍 Проверка статуса всех сервисов..."

services=(
    "http://localhost:5001/health:Окконатор"
    "http://localhost:5002/health:Swipe"
    "http://localhost:5003/health:Movie Recommendation"
)

for service in "${services[@]}"; do
    url=$(echo $service | cut -d: -f1-2)
    name=$(echo $service | cut -d: -f3)
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name: OK"
    else
        echo "❌ $name: НЕ ДОСТУПЕН"
    fi
done

echo ""
echo "🎉 Все сервисы запущены!"
echo ""
echo "📋 Доступные сервисы:"
echo "  - Основное приложение: http://localhost:5000"
echo "  - Окконатор: http://localhost:5001"
echo "  - Swipe: http://localhost:5002"
echo "  - Movie Recommendation: http://localhost:5003"
echo ""
echo "🛑 Для остановки всех сервисов используйте: ./stop_all_services.sh"
echo ""
echo "🎬 Запуск основного приложения..."
python app.py
