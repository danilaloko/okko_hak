#!/usr/bin/env python3
"""
Скрипт для запуска Movie Swiper приложения
"""

from app import app

if __name__ == '__main__':
    print("🎬 Запуск Movie Swiper...")
    print("📱 Откройте браузер и перейдите по адресу: http://localhost:5000")
    print("💡 Свайпайте фильмы влево (не нравится) или вправо (нравится)")
    print("🔄 Нажмите Ctrl+C для остановки сервера")
    
    app.run(debug=True, host='0.0.0.0', port=5000)


