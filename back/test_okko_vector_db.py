#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для создания векторной базы данных из первых 10 записей Okko
"""

import pandas as pd
import numpy as np
import json
import re
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_okko_data_test(parquet_path: str = "data/catalog_okko.parquet", limit: int = 5000) -> pd.DataFrame:
    """Загружает первые N записей из каталога Okko для тестирования"""
    logger.info(f"Загружаем первые {limit} записей из {parquet_path}")
    
    try:
        df = pd.read_parquet(parquet_path)
        df_test = df.head(limit).copy()
        logger.info(f"Загружено {len(df_test)} записей для тестирования")
        return df_test
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        raise

def clean_text(text: str) -> str:
    """Очищает текст от лишних символов и нормализует"""
    if pd.isna(text) or text == "":
        return ""
    
    # Убираем лишние пробелы и переносы строк
    text = re.sub(r'\s+', ' ', str(text).strip())
    
    # Убираем HTML теги если есть
    text = re.sub(r'<[^>]+>', '', text)
    
    return text

def create_enhanced_text(row: pd.Series) -> str:
    """Создает улучшенный текст для эмбеддингов с контекстом"""
    parts = []
    
    # Функция для безопасного получения строки
    def safe_str(value):
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) == 0:
                return ""
            return str(value)
        if pd.isna(value):
            return ""
        return str(value)
    
    # Основная информация
    serial_name = safe_str(row["serial_name"])
    if serial_name and serial_name.strip():
        parts.append(f"Название: {clean_text(serial_name)}")
    
    # Описание (самое важное для RAG)
    description = safe_str(row["description"])
    if description and description.strip():
        desc = clean_text(description)
        # Ограничиваем длину описания для лучшего качества эмбеддингов
        if len(desc) > 500:
            desc = desc[:500] + "..."
        parts.append(f"Описание: {desc}")
    
    # Жанры с контекстом
    genres = safe_str(row["genres"])
    if genres and genres.strip():
        genres_clean = clean_text(genres)
        parts.append(f"Жанры: {genres_clean}")
    
    # Актеры (первые 5 для экономии места)
    actors = safe_str(row["actors"])
    if actors and actors.strip():
        actors_clean = clean_text(actors)
        # Берем только первых 5 актеров
        actors_list = [actor.strip() for actor in actors_clean.split(",") if actor.strip()][:5]
        if actors_list:
            parts.append(f"В ролях: {', '.join(actors_list)}")
    
    # Режиссер
    director = safe_str(row["director"])
    if director and director.strip():
        director_clean = clean_text(director)
        parts.append(f"Режиссер: {director_clean}")
    
    # Страна и студия
    country = safe_str(row["country"])
    if country and country.strip():
        country_clean = clean_text(country)
        parts.append(f"Страна: {country_clean}")
    
    studio = safe_str(row["studio_name"])
    if studio and studio.strip():
        studio_clean = clean_text(studio)
        parts.append(f"Студия: {studio_clean}")
    
    # Тип контента
    content_type = safe_str(row["content_type"])
    if content_type and content_type.strip():
        content_type_clean = clean_text(content_type)
        parts.append(f"Тип: {content_type_clean}")
    
    # Возрастной рейтинг
    if pd.notna(row["age_rating"]) and row["age_rating"] > 0:
        parts.append(f"Возрастной рейтинг: {row['age_rating']}+")
    
    return " | ".join(parts)

def create_metadata(row: pd.Series, index: int) -> Dict[str, Any]:
    """Создает структурированные метаданные для фильтрации"""
    
    # Функция для безопасного получения строки
    def safe_str(value):
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) == 0:
                return ""
            return str(value)
        if pd.isna(value):
            return ""
        return str(value)
    
    metadata = {
        "id": index,
        "title": clean_text(safe_str(row["serial_name"])),
        "content_type": clean_text(safe_str(row["content_type"])),
        "country": clean_text(safe_str(row["country"])),
        "age_rating": float(row["age_rating"]) if pd.notna(row["age_rating"]) else None,
        "url": safe_str(row["url"]),
        "studio": clean_text(safe_str(row["studio_name"])),
        "director": clean_text(safe_str(row["director"])),
        "release_date": safe_str(row["release_date"]) if pd.notna(row["release_date"]) else None
    }
    
    # Обработка жанров
    genres_str = safe_str(row["genres"])
    if genres_str and genres_str.strip():
        genres_text = clean_text(genres_str)
        metadata["genres"] = [genre.strip() for genre in genres_text.split(",") if genre.strip()]
    else:
        metadata["genres"] = []
    
    # Обработка актеров
    actors_str = safe_str(row["actors"])
    if actors_str and actors_str.strip():
        actors_text = clean_text(actors_str)
        metadata["actors"] = [actor.strip() for actor in actors_text.split(",") if actor.strip()]
    else:
        metadata["actors"] = []
    
    return metadata

def create_embeddings(df: pd.DataFrame, model_kind: str, model) -> np.ndarray:
    """Создает эмбеддинги для всех фильмов"""
    logger.info("Создаем эмбеддинги...")
    
    texts = []
    for idx, row in df.iterrows():
        text = create_enhanced_text(row)
        texts.append(text)
        logger.info(f"Текст {idx}: {text[:100]}...")
    
    logger.info(f"Создаем эмбеддинги для {len(texts)} фильмов...")
    
    if model_kind == "st":
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    else:
        embeddings = model.fit_transform(texts).astype(np.float32)
        A = embeddings.toarray()
        norms = np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
        embeddings = A / norms
    
    logger.info(f"Создано эмбеддингов размерности: {embeddings.shape}")
    return embeddings

def analyze_okko_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Анализирует данные Okko и создает метаданные"""
    logger.info("Анализируем данные Okko...")
    
    # Анализ жанров
    all_genres = []
    for genres_str in df["genres"].dropna():
        if isinstance(genres_str, str):
            genres = [g.strip() for g in genres_str.split(",") if g.strip()]
            all_genres.extend(genres)
    
    genre_counts = pd.Series(all_genres).value_counts().to_dict()
    unique_genres = list(genre_counts.keys())
    
    # Анализ типов контента
    content_types = df["content_type"].astype(str).value_counts().to_dict()
    
    # Анализ стран
    countries = df["country"].astype(str).value_counts().to_dict()
    
    # Анализ студий
    studios = df["studio_name"].astype(str).value_counts().to_dict()
    
    # Анализ возрастных рейтингов
    age_ratings = df["age_rating"].dropna()
    age_rating_stats = {
        "min": float(age_ratings.min()) if len(age_ratings) > 0 else None,
        "max": float(age_ratings.max()) if len(age_ratings) > 0 else None,
        "mean": float(age_ratings.mean()) if len(age_ratings) > 0 else None
    }
    
    # Анализ актеров
    all_actors = []
    for actors_str in df["actors"].dropna():
        if isinstance(actors_str, str):
            actors = [a.strip() for a in actors_str.split(",") if a.strip()]
            all_actors.extend(actors)
    
    actor_counts = pd.Series(all_actors).value_counts().to_dict()
    top_actors = list(actor_counts.keys())[:50]  # Топ 50 актеров
    
    metadata = {
        "total_movies": len(df),
        "genres": unique_genres,
        "genre_counts": genre_counts,
        "content_types": content_types,
        "countries": countries,
        "studios": studios,
        "age_rating_stats": age_rating_stats,
        "top_actors": top_actors,
        "actor_counts": {k: v for k, v in list(actor_counts.items())[:100]},
        "created_at": datetime.now().isoformat(),
        "data_source": "okko_catalog_test"
    }
    
    logger.info(f"Найдено {len(unique_genres)} уникальных жанров")
    logger.info(f"Найдено {len(content_types)} типов контента")
    logger.info(f"Найдено {len(countries)} стран")
    
    return metadata

def save_vector_db(df: pd.DataFrame, embeddings: np.ndarray, metadata: Dict[str, Any], 
                  output_dir: str = "data") -> None:
    """Сохраняет векторную базу данных"""
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Сохраняем векторную базу данных...")
    
    # Создаем метаданные для каждой записи
    records_metadata = []
    for idx, row in df.iterrows():
        record_meta = create_metadata(row, idx)
        records_metadata.append(record_meta)
        logger.info(f"Метаданные {idx}: {record_meta['title']}")
    
    # Сохраняем данные
    df.to_pickle(f"{output_dir}/okko_test_movies_df.pkl")
    np.save(f"{output_dir}/okko_test_embeddings.npy", embeddings)
    
    # Сохраняем общие метаданные
    with open(f"{output_dir}/okko_test_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # Сохраняем метаданные записей
    with open(f"{output_dir}/okko_test_records_metadata.json", "w", encoding="utf-8") as f:
        json.dump(records_metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Сохранено в директории: {output_dir}")
    logger.info(f"  - okko_test_movies_df.pkl: {len(df)} фильмов")
    logger.info(f"  - okko_test_embeddings.npy: эмбеддинги {embeddings.shape}")
    logger.info(f"  - okko_test_metadata.json: общие метаданные")
    logger.info(f"  - okko_test_records_metadata.json: метаданные записей")

def load_model():
    """Загружает модель для создания эмбеддингов"""
    logger.info("Загружаем модель...")
    
    try:
        from sentence_transformers import SentenceTransformer
        # Используем более мощную модель для лучшего качества
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        model_kind = "st"
        logger.info("Используем SentenceTransformer (multilingual)")
        return model, model_kind
    except Exception as e:
        logger.warning(f"Не удалось загрузить SentenceTransformer: {e}")
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            model = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
            model_kind = "tfidf"
            logger.info("Используем TF-IDF")
            return model, model_kind
        except Exception as e2:
            logger.error(f"Не удалось загрузить ни одну модель: {e2}")
            raise

def main():
    """Основная функция"""
    logger.info("=== ТЕСТОВОЕ СОЗДАНИЕ ВЕКТОРНОЙ БД ИЗ OKKO ДАННЫХ ===")
    
    try:
        # Загрузка данных (только первые 1000 записей)
        df = load_okko_data_test(limit=1000)
        
        # Показываем первые записи
        logger.info("Первые записи:")
        for idx, row in df.iterrows():
            logger.info(f"  {idx}: {row['serial_name']}")
        
        # Анализ данных
        metadata = analyze_okko_data(df)
        
        # Загрузка модели
        model, model_kind = load_model()
        
        # Создание эмбеддингов
        embeddings = create_embeddings(df, model_kind, model)
        
        # Сохранение
        save_vector_db(df, embeddings, metadata)
        
        logger.info("=== ТЕСТ ЗАВЕРШЕН ===")
        logger.info("Тестовая векторная база данных Okko создана!")
        
        # Выводим статистику
        print(f"\n📊 СТАТИСТИКА ТЕСТА:")
        print(f"   • Тестовых фильмов: {len(df)}")
        print(f"   • Размерность эмбеддингов: {embeddings.shape}")
        print(f"   • Уникальных жанров: {len(metadata['genres'])}")
        print(f"   • Типов контента: {len(metadata['content_types'])}")
        print(f"   • Стран: {len(metadata['countries'])}")
        
    except Exception as e:
        logger.error(f"Ошибка при создании тестовой векторной БД: {e}")
        raise

if __name__ == "__main__":
    main()
