#!/bin/bash

# Скрипт для запуска микросервиса Окконатора
# Запускает отдельный процесс для обработки рекомендаций фильмов

echo "Запуск микросервиса Окконатора..."

# Активируем виртуальное окружение
source env/bin/activate

# Запускаем микросервис в фоновом режиме
python okkonator_service.py &

# Сохраняем PID процесса
echo $! > okkonator_service.pid

echo "Микросервис Окконатора запущен (PID: $(cat okkonator_service.pid))"
echo "Сервис доступен на http://localhost:5001"
echo "Для остановки выполните: kill \$(cat okkonator_service.pid)"
