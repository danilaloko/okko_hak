#!/bin/bash

# Скрипт для остановки микросервиса Окконатора

if [ -f "okkonator_service.pid" ]; then
    PID=$(cat okkonator_service.pid)
    echo "Остановка микросервиса Окконатора (PID: $PID)..."
    
    if kill $PID 2>/dev/null; then
        echo "Микросервис Окконатора остановлен"
        rm okkonator_service.pid
    else
        echo "Процесс не найден или уже остановлен"
        rm okkonator_service.pid
    fi
else
    echo "PID файл не найден. Микросервис может быть не запущен."
fi
