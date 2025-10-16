#!/usr/bin/env python3
"""
Скрипт для анализа IMDB.csv и создания векторной базы данных
"""

import pandas as pd
import numpy as np
import pickle
import json
from collections import Counter
import re

def analyze_imdb_data(csv_path="../data/IMBD.csv"):
    """Анализирует данные IMDB и извлекает все параметры"""
    print("Загружаем данные...")
    df = pd.read_csv(csv_path)
    
    print(f"Загружено {len(df)} записей")
    
    # Очистка и обработка данных
    df["genre"] = df["genre"].fillna("")
    df["description"] = df["description"].fillna("")
    df["stars"] = df["stars"].fillna("")
    
    # Извлечение года
    df["year"] = df["year"].str.extract(r'(\d{4})').astype(float)
    df["year"] = df["year"].fillna(2020)
    
    # Обработка duration
    df["duration"] = df["duration"].str.replace(" min", "").str.replace(" min", "")
    df["duration"] = pd.to_numeric(df["duration"], errors='coerce')
    df["duration"] = df["duration"].fillna(90)
    
    # Обработка rating
    df["rating"] = pd.to_numeric(df["rating"], errors='coerce')
    df["rating"] = df["rating"].fillna(6.0)
    
    # Обработка votes
    df["votes"] = df["votes"].str.replace(",", "").astype(float)
    df["votes"] = df["votes"].fillna(1000)
    
    # Создание поля violence
    violence_keywords = ["R", "TV-MA", "NC-17"]
    violence_genres = ["Horror", "Thriller", "Crime", "Action"]
    df["violence"] = 0
    df.loc[df["certificate"].isin(violence_keywords), "violence"] = 1
    df.loc[df["genre"].str.contains("|".join(violence_genres), case=False, na=False), "violence"] = 1
    
    # Анализ жанров
    print("\n=== АНАЛИЗ ЖАНРОВ ===")
    all_genres = set()
    genre_counts = Counter()
    
    for genres in df["genre"].dropna():
        for genre in str(genres).split(", "):
            genre = genre.strip()
            if genre:
                all_genres.add(genre)
                genre_counts[genre] += 1
    
    print(f"Найдено {len(all_genres)} уникальных жанров:")
    for genre, count in genre_counts.most_common():
        print(f"  {genre}: {count} фильмов")
    
    # Анализ сертификатов
    print("\n=== АНАЛИЗ СЕРТИФИКАТОВ ===")
    cert_counts = df["certificate"].value_counts()
    print("Сертификаты:")
    for cert, count in cert_counts.items():
        print(f"  {cert}: {count} фильмов")
    
    # Анализ рейтингов
    print("\n=== АНАЛИЗ РЕЙТИНГОВ ===")
    print(f"Диапазон: {df['rating'].min():.1f} - {df['rating'].max():.1f}")
    print(f"Средний рейтинг: {df['rating'].mean():.1f}")
    
    # Анализ длительности
    print("\n=== АНАЛИЗ ДЛИТЕЛЬНОСТИ ===")
    print(f"Диапазон: {df['duration'].min():.0f} - {df['duration'].max():.0f} минут")
    print(f"Средняя длительность: {df['duration'].mean():.0f} минут")
    
    # Анализ годов
    print("\n=== АНАЛИЗ ГОДОВ ===")
    print(f"Диапазон: {df['year'].min():.0f} - {df['year'].max():.0f}")
    
    # Анализ актеров
    print("\n=== АНАЛИЗ АКТЕРОВ ===")
    all_actors = set()
    actor_counts = Counter()
    
    for stars in df["stars"].dropna():
        # Очистка строки с актерами
        stars_clean = re.sub(r"\[|\]|'|\"", "", str(stars))
        stars_clean = re.sub(r"Stars:", "", stars_clean)
        stars_clean = re.sub(r"\s+\|\s+", ", ", stars_clean)
        
        for actor in stars_clean.split(", "):
            actor = actor.strip()
            if actor and len(actor) > 2:  # фильтруем короткие строки
                all_actors.add(actor)
                actor_counts[actor] += 1
    
    print(f"Найдено {len(all_actors)} уникальных актеров")
    print("Топ-20 актеров:")
    for actor, count in actor_counts.most_common(20):
        print(f"  {actor}: {count} фильмов")
    
    return df, {
        "genres": list(all_genres),
        "certificates": list(cert_counts.index),
        "rating_range": (df["rating"].min(), df["rating"].max()),
        "duration_range": (df["duration"].min(), df["duration"].max()),
        "year_range": (df["year"].min(), df["year"].max()),
        "top_actors": [actor for actor, _ in actor_counts.most_common(50)],
        "genre_counts": dict(genre_counts),
        "actor_counts": dict(actor_counts)
    }

def create_embeddings(df, model_kind, model):
    """Создает эмбеддинги для всех фильмов"""
    print("\n=== СОЗДАНИЕ ЭМБЕДДИНГОВ ===")
    
    # Создаем тексты для эмбеддингов
    texts = []
    for _, row in df.iterrows():
        text_parts = []
        
        # Название
        if pd.notna(row["title"]):
            text_parts.append(str(row["title"]))
        
        # Описание
        if pd.notna(row["description"]):
            text_parts.append(str(row["description"]))
        
        # Жанры
        if pd.notna(row["genre"]):
            text_parts.append(str(row["genre"]))
        
        # Актеры (первые 3)
        if pd.notna(row["stars"]):
            stars_clean = re.sub(r"\[|\]|'|\"", "", str(row["stars"]))
            stars_clean = re.sub(r"Stars:", "", stars_clean)
            stars_clean = re.sub(r"\s+\|\s+", ", ", stars_clean)
            actors = [actor.strip() for actor in stars_clean.split(", ") if actor.strip()][:3]
            if actors:
                text_parts.append(" ".join(actors))
        
        texts.append(" ".join(text_parts))
    
    print(f"Создаем эмбеддинги для {len(texts)} фильмов...")
    
    if model_kind == "st":
        embeddings = model.encode(texts, normalize_embeddings=True)
    else:
        embeddings = model.fit_transform(texts).astype(np.float32)
        A = embeddings.toarray()
        norms = np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
        embeddings = A / norms
    
    print(f"Создано эмбеддингов размерности: {embeddings.shape}")
    return embeddings

def save_vector_db(df, embeddings, metadata, output_dir="../data"):
    """Сохраняет векторную базу данных"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n=== СОХРАНЕНИЕ ВЕКТОРНОЙ БД ===")
    
    # Сохраняем данные
    df.to_pickle(f"{output_dir}/movies_df.pkl")
    np.save(f"{output_dir}/embeddings.npy", embeddings)
    
    with open(f"{output_dir}/metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"Сохранено в директории: {output_dir}")
    print(f"  - movies_df.pkl: {len(df)} фильмов")
    print(f"  - embeddings.npy: {embeddings.shape}")
    print(f"  - metadata.json: метаданные")

def main():
    print("=== АНАЛИЗ IMDB ДАННЫХ И СОЗДАНИЕ ВЕКТОРНОЙ БД ===")
    
    # Анализ данных
    df, metadata = analyze_imdb_data()
    
    # Создание модели
    print("\n=== ЗАГРУЗКА МОДЕЛИ ===")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        model_kind = "st"
        print("Используем SentenceTransformer")
    except Exception as e:
        from sklearn.feature_extraction.text import TfidfVectorizer
        model = TfidfVectorizer(max_features=5000)
        model_kind = "tfidf"
        print("Используем TF-IDF")
    
    # Создание эмбеддингов
    embeddings = create_embeddings(df, model_kind, model)
    
    # Сохранение
    save_vector_db(df, embeddings, metadata)
    
    print("\n=== ГОТОВО ===")
    print("Векторная база данных создана и готова к использованию!")

if __name__ == "__main__":
    main()
