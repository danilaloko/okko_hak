#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обработки данных фильмов согласно статье с Habr
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import re
import os

def load_movies_data():
    """Загружает и обрабатывает данные о фильмах"""
    print("Загружаем данные о фильмах...")
    
    # Проверяем наличие файла movies.csv
    if not os.path.exists('movies.csv'):
        print("ОШИБКА: Файл movies.csv не найден!")
        print("Пожалуйста, скачайте датасет TMDB + IMDB Movies Dataset 2024")
        print("и поместите его в корневую папку проекта как movies.csv")
        return None
    
    movies = pd.read_csv(
        'movies.csv',
        usecols=['id', 'title', 'release_date', 'revenue', 'status',
                'imdb_id', 'original_language', 'original_title', 'overview',
                'tagline', 'genres', 'production_companies',
                'production_countries',
                'spoken_languages', 'cast', 'director', 'writers',
                'imdb_rating', 'imdb_votes']
    )
    
    print(f"Загружено {len(movies)} фильмов")
    return movies

def clean_movies_data(movies):
    """Очищает данные о фильмах"""
    print("Очищаем данные...")
    
    # Удаляем строки с пустыми колонками
    movies.dropna(subset=[
        'title', 'overview', 'genres', 'release_date', 'status',
        'cast', 'director', 'writers', 'imdb_id'], 
        inplace=True
    )
    
    # Оставляем только вышедшие фильмы с доходом
    movies = movies[movies['status'] == 'Released']
    movies = movies[movies['revenue'] > 0]
    movies.drop(['status', 'revenue'], axis=1, inplace=True)
    movies.reset_index(drop=True, inplace=True)
    
    # Заполняем пропущенные значения
    movies.fillna({'imdb_rating': 0, 'imdb_votes': 0}, inplace=True)
    movies['tagline'] = movies['tagline'].fillna('')
    
    print(f"После очистки осталось {len(movies)} фильмов")
    return movies

def load_top_actors():
    """Загружает топ актеров"""
    print("Загружаем данные о топ актерах...")
    
    if not os.path.exists('actors.csv'):
        print("ОШИБКА: Файл actors.csv не найден!")
        print("Пожалуйста, скачайте датасет Top 100 Greatest Hollywood Actors")
        print("и поместите его в корневую папку проекта как actors.csv")
        return None
    
    actors = pd.read_csv('actors.csv')
    
    # Выделяем год рождения
    actors['Year of Birth'] = actors['Date of Birth'].apply(
        lambda d: d.split()[-1] if pd.notna(d) else '1900'
    )
    
    # Сортируем по году рождения и берем первых 50 актеров
    actors.sort_values('Year of Birth', ascending=False, inplace=True)
    actor_set = set(actors.head(50)['Name'])
    
    print(f"Загружено {len(actor_set)} топ актеров")
    return actor_set

def filter_movies_by_actors(movies, actor_set):
    """Фильтрует фильмы по наличию топ актеров"""
    print("Фильтруем фильмы по топ актерам...")
    
    def actors_intersect(actors_str):
        """Проверяем пересечение актеров"""
        if pd.isna(actors_str):
            return False
        actors = set(actors_str.split(', '))
        return bool(actors.intersection(actor_set))
    
    # Отбираем фильмы для теста
    movies['to_test'] = movies['cast'].apply(actors_intersect)
    df = movies[movies['to_test']]
    df.reset_index(drop=True, inplace=True)
    
    print(f"Отобрано {len(df)} фильмов с топ актерами")
    return df

def cluster_franchises(df):
    """Объединяет франшизы через кластеризацию"""
    print("Объединяем франшизы...")
    
    # Создаем векторы для названий фильмов
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=1000,
        ngram_range=(1, 2)
    )
    
    # Векторизуем названия
    title_vectors = vectorizer.fit_transform(df['title'].fillna(''))
    
    # Кластеризация
    n_clusters = min(50, len(df) // 10)  # Примерно 10 фильмов на кластер
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df['franchise_cluster'] = kmeans.fit_predict(title_vectors)
    
    print(f"Создано {n_clusters} кластеров франшиз")
    return df

def save_processed_data(df):
    """Сохраняет обработанные данные"""
    print("Сохраняем обработанные данные...")
    
    # Сохраняем в CSV
    df.to_csv('processed_movies.csv', index=False)
    
    # Создаем файл с информацией о кластерах
    cluster_info = df.groupby('franchise_cluster').agg({
        'title': 'count',
        'imdb_rating': 'mean'
    }).rename(columns={'title': 'count', 'imdb_rating': 'avg_rating'})
    
    cluster_info.to_csv('franchise_clusters.csv')
    
    print("Данные сохранены в processed_movies.csv и franchise_clusters.csv")

def main():
    """Основная функция"""
    print("=== Парсинг и обработка данных о фильмах ===")
    
    # Загружаем данные
    movies = load_movies_data()
    if movies is None:
        return
    
    # Очищаем данные
    movies = clean_movies_data(movies)
    
    # Загружаем топ актеров
    actor_set = load_top_actors()
    if actor_set is None:
        return
    
    # Фильтруем фильмы
    df = filter_movies_by_actors(movies, actor_set)
    
    # Объединяем франшизы
    df = cluster_franchises(df)
    
    # Сохраняем результат
    save_processed_data(df)
    
    print("=== Обработка завершена ===")
    print(f"Итого обработано: {len(df)} фильмов")
    print(f"Создано кластеров франшиз: {df['franchise_cluster'].nunique()}")

if __name__ == "__main__":
    main()



