#!/bin/bash

# Скрипт для остановки всех микросервисов

echo "🛑 Остановка всех микросервисов Okko Hak..."

echo ""
echo "1️⃣  Остановка микросервиса подбора фильмов..."
./stop_movie_recommendation_service.sh

echo ""
echo "2️⃣  Остановка микросервиса Swipe..."
./stop_swipe_service.sh

echo ""
echo "3️⃣  Остановка микросервиса Окконатора..."
./stop_okkonator_service.sh

echo ""
echo "🔍 Проверка, что все порты свободны..."

ports=(5001 5002 5003)
for port in "${ports[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Порт $port все еще занят"
        echo "🔍 Процессы на порту $port:"
        lsof -Pi :$port -sTCP:LISTEN
    else
        echo "✅ Порт $port свободен"
    fi
done

echo ""
echo "🎉 Все микросервисы остановлены!"
echo "📋 Логи сохранены в папке logs/"
