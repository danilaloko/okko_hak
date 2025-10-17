#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания векторной базы данных из каталога Okko
Оптимизирован для RAG (Retrieval-Augmented Generation)
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

def load_okko_data(parquet_path: str = "../data/catalog_okko.parquet") -> pd.DataFrame:
    """Загружает данные из каталога Okko"""
    logger.info(f"Загружаем данные из {parquet_path}")
    
    try:
        df = pd.read_parquet(parquet_path)
        logger.info(f"Загружено {len(df)} записей")
        return df
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
    
    # Основная информация
    if pd.notna(row["serial_name"]) and row["serial_name"].strip():
        parts.append(f"Название: {clean_text(row['serial_name'])}")
    
    # Описание (самое важное для RAG)
    if pd.notna(row["description"]) and row["description"].strip():
        desc = clean_text(row["description"])
        # Ограничиваем длину описания для лучшего качества эмбеддингов
        if len(desc) > 500:
            desc = desc[:500] + "..."
        parts.append(f"Описание: {desc}")
    
    # Жанры с контекстом
    if pd.notna(row["genres"]) and row["genres"].strip():
        genres = clean_text(row["genres"])
        parts.append(f"Жанры: {genres}")
    
    # Актеры (первые 5 для экономии места)
    if pd.notna(row["actors"]) and row["actors"].strip():
        actors = clean_text(row["actors"])
        # Берем только первых 5 актеров
        actors_list = [actor.strip() for actor in actors.split(",") if actor.strip()][:5]
        if actors_list:
            parts.append(f"В ролях: {', '.join(actors_list)}")
    
    # Режиссер
    if pd.notna(row["director"]) and row["director"].strip():
        director = clean_text(row["director"])
        parts.append(f"Режиссер: {director}")
    
    # Страна и студия
    if pd.notna(row["country"]) and row["country"].strip():
        country = clean_text(row["country"])
        parts.append(f"Страна: {country}")
    
    if pd.notna(row["studio_name"]) and row["studio_name"].strip():
        studio = clean_text(row["studio_name"])
        parts.append(f"Студия: {studio}")
    
    # Тип контента
    if pd.notna(row["content_type"]) and row["content_type"].strip():
        content_type = clean_text(row["content_type"])
        parts.append(f"Тип: {content_type}")
    
    # Возрастной рейтинг
    if pd.notna(row["age_rating"]) and row["age_rating"] > 0:
        parts.append(f"Возрастной рейтинг: {row['age_rating']}+")
    
    return " | ".join(parts)

def create_metadata(row: pd.Series, index: int) -> Dict[str, Any]:
    """Создает структурированные метаданные для фильтрации"""
    metadata = {
        "id": index,
        "title": clean_text(row["serial_name"]) if pd.notna(row["serial_name"]) else "",
        "content_type": clean_text(row["content_type"]) if pd.notna(row["content_type"]) else "",
        "country": clean_text(row["country"]) if pd.notna(row["country"]) else "",
        "age_rating": float(row["age_rating"]) if pd.notna(row["age_rating"]) else None,
        "url": row["url"] if pd.notna(row["url"]) else "",
        "studio": clean_text(row["studio_name"]) if pd.notna(row["studio_name"]) else "",
        "director": clean_text(row["director"]) if pd.notna(row["director"]) else "",
        "release_date": row["release_date"] if pd.notna(row["release_date"]) else None
    }
    
    # Обработка жанров
    if pd.notna(row["genres"]) and row["genres"].strip():
        genres_text = clean_text(row["genres"])
        metadata["genres"] = [genre.strip() for genre in genres_text.split(",") if genre.strip()]
    else:
        metadata["genres"] = []
    
    # Обработка актеров
    if pd.notna(row["actors"]) and row["actors"].strip():
        actors_text = clean_text(row["actors"])
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
    content_types = df["content_type"].value_counts().to_dict()
    
    # Анализ стран
    countries = df["country"].value_counts().to_dict()
    
    # Анализ студий
    studios = df["studio_name"].value_counts().to_dict()
    
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
        "data_source": "okko_catalog"
    }
    
    logger.info(f"Найдено {len(unique_genres)} уникальных жанров")
    logger.info(f"Найдено {len(content_types)} типов контента")
    logger.info(f"Найдено {len(countries)} стран")
    
    return metadata

def save_vector_db(df: pd.DataFrame, embeddings: np.ndarray, metadata: Dict[str, Any], 
                  output_dir: str = "../data") -> None:
    """Сохраняет векторную базу данных"""
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Сохраняем векторную базу данных...")
    
    # Создаем метаданные для каждой записи
    records_metadata = []
    for idx, row in df.iterrows():
        record_meta = create_metadata(row, idx)
        records_metadata.append(record_meta)
    
    # Сохраняем данные
    df.to_pickle(f"{output_dir}/okko_movies_df.pkl")
    np.save(f"{output_dir}/okko_embeddings.npy", embeddings)
    
    # Сохраняем общие метаданные
    with open(f"{output_dir}/okko_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # Сохраняем метаданные записей
    with open(f"{output_dir}/okko_records_metadata.json", "w", encoding="utf-8") as f:
        json.dump(records_metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Сохранено в директории: {output_dir}")
    logger.info(f"  - okko_movies_df.pkl: {len(df)} фильмов")
    logger.info(f"  - okko_embeddings.npy: эмбеддинги {embeddings.shape}")
    logger.info(f"  - okko_metadata.json: общие метаданные")
    logger.info(f"  - okko_records_metadata.json: метаданные записей")

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
    logger.info("=== СОЗДАНИЕ ВЕКТОРНОЙ БД ИЗ OKKO ДАННЫХ ===")
    
    try:
        # Загрузка данных
        df = load_okko_data()
        
        # Анализ данных
        metadata = analyze_okko_data(df)
        
        # Загрузка модели
        model, model_kind = load_model()
        
        # Создание эмбеддингов
        embeddings = create_embeddings(df, model_kind, model)
        
        # Сохранение
        save_vector_db(df, embeddings, metadata)
        
        logger.info("=== ГОТОВО ===")
        logger.info("Векторная база данных Okko создана и готова к использованию!")
        
        # Выводим статистику
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   • Всего фильмов: {len(df)}")
        print(f"   • Размерность эмбеддингов: {embeddings.shape}")
        print(f"   • Уникальных жанров: {len(metadata['genres'])}")
        print(f"   • Типов контента: {len(metadata['content_types'])}")
        print(f"   • Стран: {len(metadata['countries'])}")
        
    except Exception as e:
        logger.error(f"Ошибка при создании векторной БД: {e}")
        raise

if __name__ == "__main__":
    main()
