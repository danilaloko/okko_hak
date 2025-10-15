#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для скачивания необходимых датасетов
"""

import requests
import os
import zipfile
from urllib.parse import urlparse

def download_file(url, filename):
    """Скачивает файл по URL"""
    print(f"Скачиваем {filename}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Файл {filename} скачан успешно")
        return True
    except Exception as e:
        print(f"Ошибка при скачивании {filename}: {e}")
        return False

def extract_zip(zip_path, extract_to="."):
    """Распаковывает ZIP файл"""
    print(f"Распаковываем {zip_path}...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Файл {zip_path} распакован успешно")
        return True
    except Exception as e:
        print(f"Ошибка при распаковке {zip_path}: {e}")
        return False

def main():
    """Основная функция для скачивания датасетов"""
    print("=== Скачивание датасетов ===")
    
    # Создаем папку для данных
    os.makedirs("data", exist_ok=True)
    
    # Инструкции для пользователя
    print("\nДля работы скрипта необходимы следующие датасеты:")
    print("\n1. TMDB + IMDB Movies Dataset 2024:")
    print("   - Найдите на Kaggle: 'TMDB + IMDB Movies Dataset 2024'")
    print("   - Скачайте файл и переименуйте его в 'movies.csv'")
    print("   - Поместите в корневую папку проекта")
    
    print("\n2. Top 100 Greatest Hollywood Actors:")
    print("   - Найдите датасет с топ актерами")
    print("   - Создайте файл actors.csv с колонками:")
    print("     - Name: имя актера")
    print("     - Date of Birth: дата рождения")
    print("   - Поместите в корневую папку проекта")
    
    print("\nПример структуры actors.csv:")
    print("Name,Date of Birth")
    print("Marlon Brando,April 3 1924")
    print("Al Pacino,April 25 1940")
    print("Robert De Niro,August 17 1943")
    
    print("\nПосле скачивания датасетов запустите:")
    print("python data_processing.py")

if __name__ == "__main__":
    main()



