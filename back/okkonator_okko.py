#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Окконатор для работы с данными Okko
Обновленная версия для новой структуры векторной БД
"""

import sys
import numpy as np
import pandas as pd
import json
import os
import re
from typing import Dict, List, Any, Optional

ETA = 0.3
QUESTIONS_MAX = 15
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Расширенные оси для параметров Okko
AXES = [
    # Основные характеристики
    "tempo_slow", "darkness", "humor", "novelty", "violence_tol",
    
    # Жанры (адаптированы под русские названия)
    "genre_action", "genre_comedy", "genre_drama", "genre_crime", "genre_scifi",
    "genre_horror", "genre_thriller", "genre_romance", "genre_fantasy", "genre_animation",
    "genre_biography", "genre_history", "genre_mystery", "genre_adventure", "genre_sport",
    "genre_documentary", "genre_family", "genre_musical", "genre_war",
    
    # Тип контента
    "prefer_movies", "prefer_series", "prefer_shows",
    
    # Страны
    "prefer_russian", "prefer_foreign", "prefer_american", "prefer_european",
    
    # Возрастные предпочтения
    "family_friendly", "mature_content",
    
    # Качество и популярность
    "high_quality", "popular_content", "recent_content", "classic_content"
]

QUESTIONS = [
    # Основные предпочтения
    {"id":"q1", "text":"Сейчас хочется чего-то лёгкого и позитивного?",
     "targets":{"darkness":-1, "humor":+1, "family_friendly":+1}},
    {"id":"q2", "text":"Предпочитаете медленный, атмосферный темп?",
     "targets":{"tempo_slow":+1}},
    {"id":"q3", "text":"Юмор и комедия обязательны сегодня?",
     "targets":{"humor":+1, "genre_comedy":+1}},
    {"id":"q4", "text":"Мрачные и тяжёлые темы — нормально?",
     "targets":{"darkness":+1, "mature_content":+1}},
    {"id":"q5", "text":"Хотите что-то нестандартное и экспериментальное?",
     "targets":{"novelty":+1}},
    {"id":"q6", "text":"Готовы к жёстким сценам (насилие, экшн)?",
     "targets":{"violence_tol":+1, "mature_content":+1}},
    
    # Тип контента
    {"id":"q7", "text":"Фильмы предпочитаете сериалам?",
     "targets":{"prefer_movies":+1, "prefer_series":-1}},
    {"id":"q8", "text":"Сериалы интереснее фильмов?",
     "targets":{"prefer_series":+1, "prefer_movies":-1}},
    
    # Жанровые предпочтения
    {"id":"q9", "text":"Тянет к экшну и приключениям?",
     "targets":{"genre_action":+1, "genre_adventure":+1}},
    {"id":"q10","text":"Криминал и детективы интереснее фантастики?",
     "targets":{"genre_crime":+1, "genre_mystery":+1, "genre_scifi":-1}},
    {"id":"q11","text":"Хочется ужастик или триллер?",
     "targets":{"genre_horror":+1, "genre_thriller":+1}},
    {"id":"q12","text":"Романтика тоже подойдёт?",
     "targets":{"genre_romance":+1}},
    {"id":"q13","text":"Фэнтези или анимация интересны?",
     "targets":{"genre_fantasy":+1, "genre_animation":+1}},
    {"id":"q14","text":"Документальные фильмы привлекают?",
     "targets":{"genre_documentary":+1}},
    {"id":"q15","text":"Семейные фильмы для всех возрастов?",
     "targets":{"genre_family":+1, "family_friendly":+1}},
    
    # Страны и культура
    {"id":"q16","text":"Предпочитаете российские фильмы и сериалы?",
     "targets":{"prefer_russian":+1, "prefer_foreign":-1}},
    {"id":"q17","text":"Зарубежный контент интереснее отечественного?",
     "targets":{"prefer_foreign":+1, "prefer_russian":-1}},
    {"id":"q18","text":"Американские блокбастеры — ваш выбор?",
     "targets":{"prefer_american":+1, "popular_content":+1}},
    
    # Качество и время
    {"id":"q19","text":"Важно высокое качество и проработанность?",
     "targets":{"high_quality":+1}},
    {"id":"q20","text":"Свежие новинки или проверенная классика?",
     "targets":{"recent_content":+1, "classic_content":-1}},
]

LIKERT = {
    "1": -2,   # нет
    "2": -1,   # скорее нет
    "3":  0,   # не знаю
    "4":  1,   # скорее да
    "5":  2,   # да
}

def safe_str(value):
    """Безопасное преобразование в строку"""
    if pd.isna(value):
        return ""
    if isinstance(value, (list, tuple, np.ndarray)):
        if len(value) == 0:
            return ""
        return str(value)
    return str(value)

def load_okko_vector_db(data_dir="data"):
    """Загружает векторную базу данных Okko"""
    try:
        # Пробуем загрузить тестовые данные сначала
        test_files = [
            f"{data_dir}/okko_test_movies_df.pkl",
            f"{data_dir}/okko_test_embeddings.npy", 
            f"{data_dir}/okko_test_metadata.json",
            f"{data_dir}/okko_test_records_metadata.json"
        ]
        
        if all(os.path.exists(f) for f in test_files):
            df = pd.read_pickle(f"{data_dir}/okko_test_movies_df.pkl")
            embeddings = np.load(f"{data_dir}/okko_test_embeddings.npy")
            
            with open(f"{data_dir}/okko_test_metadata.json", "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            with open(f"{data_dir}/okko_test_records_metadata.json", "r", encoding="utf-8") as f:
                records_metadata = json.load(f)
            
            print(f"Загружена тестовая векторная БД Okko: {len(df)} фильмов/сериалов")
            return df, embeddings, metadata, records_metadata
        
        # Пробуем загрузить полные данные
        full_files = [
            f"{data_dir}/okko_movies_df.pkl",
            f"{data_dir}/okko_embeddings.npy",
            f"{data_dir}/okko_metadata.json",
            f"{data_dir}/okko_records_metadata.json"
        ]
        
        if all(os.path.exists(f) for f in full_files):
            df = pd.read_pickle(f"{data_dir}/okko_movies_df.pkl")
            embeddings = np.load(f"{data_dir}/okko_embeddings.npy")
            
            with open(f"{data_dir}/okko_metadata.json", "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            with open(f"{data_dir}/okko_records_metadata.json", "r", encoding="utf-8") as f:
                records_metadata = json.load(f)
            
            print(f"Загружена полная векторная БД Okko: {len(df)} фильмов/сериалов")
            return df, embeddings, metadata, records_metadata
        
        print("Векторная БД Okko не найдена. Запустите build_okko_vector_db.py сначала.")
        return None, None, None, None
        
    except Exception as e:
        print(f"Ошибка загрузки векторной БД Okko: {e}")
        return None, None, None, None

def load_model():
    """Загружает модель для создания эмбеддингов"""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(MODEL_NAME)
        return ("st", model)
    except Exception as e:
        print(f"Не удалось загрузить SentenceTransformer: {e}")
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            vec = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
            return ("tfidf", vec)
        except Exception as e2:
            print(f"Не удалось загрузить TF-IDF: {e2}")
            return None, None

def create_enhanced_text_for_search(row):
    """Создает текст для поиска (аналогично функции из build_okko_vector_db.py)"""
    parts = []
    
    # Основная информация
    serial_name = safe_str(row["serial_name"])
    if serial_name and serial_name.strip():
        parts.append(f"Название: {serial_name}")
    
    # Описание
    description = safe_str(row["description"])
    if description and description.strip():
        desc = description[:500] + "..." if len(description) > 500 else description
        parts.append(f"Описание: {desc}")
    
    # Жанры
    genres = safe_str(row["genres"])
    if genres and genres.strip():
        parts.append(f"Жанры: {genres}")
    
    # Актеры
    actors = safe_str(row["actors"])
    if actors and actors.strip():
        actors_list = [actor.strip() for actor in actors.split(",") if actor.strip()][:5]
        if actors_list:
            parts.append(f"В ролях: {', '.join(actors_list)}")
    
    # Режиссер
    director = safe_str(row["director"])
    if director and director.strip():
        parts.append(f"Режиссер: {director}")
    
    # Страна
    country = safe_str(row["country"])
    if country and country.strip():
        parts.append(f"Страна: {country}")
    
    # Студия
    studio = safe_str(row["studio_name"])
    if studio and studio.strip():
        parts.append(f"Студия: {studio}")
    
    # Тип контента
    content_type = safe_str(row["content_type"])
    if content_type and content_type.strip():
        parts.append(f"Тип: {content_type}")
    
    # Возрастной рейтинг
    if pd.notna(row["age_rating"]) and row["age_rating"] > 0:
        parts.append(f"Возрастной рейтинг: {row['age_rating']}+")
    
    return " | ".join(parts)

def embed_text(text, model_kind, model):
    """Создает эмбеддинг для текста"""
    if model_kind == "st":
        v = model.encode([text], normalize_embeddings=True)[0]
        return v
    else:
        X = model.transform([text]).astype(np.float32).toarray()[0]
        v = X / (np.linalg.norm(X) + 1e-9)
        return v

def cosine_sim(a, B):
    """Вычисляет косинусное сходство"""
    return (B @ a) / (np.linalg.norm(a) + 1e-9)

def profile_keywords(theta):
    """Создает ключевые слова на основе профиля пользователя"""
    tokens = []
    
    # Основные характеристики
    if theta["tempo_slow"] > 0.2: 
        tokens += ["медленный темп", "атмосферный", "размеренный"]
    if theta["darkness"] > 0.2: 
        tokens += ["мрачный", "тёмный", "серьёзный"]
    if theta["darkness"] < -0.2: 
        tokens += ["светлый", "позитивный", "добрый"]
    if theta["humor"] > 0.2: 
        tokens += ["смешной", "комедия", "юмор"]
    if theta["novelty"] > 0.2: 
        tokens += ["необычный", "экспериментальный", "свежий"]
    
    # Жанры
    if theta["genre_action"] > 0.2: tokens += ["боевик", "экшн", "приключения"]
    if theta["genre_comedy"] > 0.2: tokens += ["комедия", "смешной", "юмористический"]
    if theta["genre_drama"] > 0.2: tokens += ["драма", "эмоциональный", "серьёзный"]
    if theta["genre_crime"] > 0.2: tokens += ["криминал", "детектив", "расследование"]
    if theta["genre_scifi"] > 0.2: tokens += ["фантастика", "научная фантастика", "будущее"]
    if theta["genre_horror"] > 0.2: tokens += ["ужасы", "страшный", "мистика"]
    if theta["genre_thriller"] > 0.2: tokens += ["триллер", "напряжение", "саспенс"]
    if theta["genre_romance"] > 0.2: tokens += ["романтика", "любовь", "отношения"]
    if theta["genre_fantasy"] > 0.2: tokens += ["фэнтези", "магия", "сказка"]
    if theta["genre_animation"] > 0.2: tokens += ["анимация", "мультфильм", "анимационный"]
    if theta["genre_documentary"] > 0.2: tokens += ["документальный", "реальные события"]
    if theta["genre_family"] > 0.2: tokens += ["семейный", "для всей семьи"]
    
    # Тип контента
    if theta["prefer_movies"] > 0.2: tokens += ["фильм", "кино"]
    if theta["prefer_series"] > 0.2: tokens += ["сериал", "многосерийный"]
    
    # Страны
    if theta["prefer_russian"] > 0.2: tokens += ["российский", "русский", "отечественный"]
    if theta["prefer_foreign"] > 0.2: tokens += ["зарубежный", "иностранный"]
    if theta["prefer_american"] > 0.2: tokens += ["американский", "голливудский"]
    
    # Качество
    if theta["high_quality"] > 0.2: tokens += ["качественный", "хорошо снятый"]
    if theta["recent_content"] > 0.2: tokens += ["новый", "современный", "свежий"]
    if theta["classic_content"] > 0.2: tokens += ["классический", "проверенный временем"]
    
    if not tokens:
        tokens = ["интересный", "качественный", "популярный"]
    
    return " ".join(tokens)

def explain_recommendation(row, theta, record_meta):
    """Объясняет, почему фильм был рекомендован"""
    bits = []
    
    # Получаем информацию о фильме
    title = safe_str(row["serial_name"])
    genres = record_meta.get("genres", [])
    content_type = record_meta.get("content_type", "")
    country = record_meta.get("country", "")
    
    # Жанровые совпадения
    genre_matches = []
    if theta["genre_action"] > 0.2 and any("боевик" in g.lower() or "экшн" in g.lower() for g in genres):
        genre_matches.append("экшн")
    if theta["genre_comedy"] > 0.2 and any("комедия" in g.lower() for g in genres):
        genre_matches.append("комедия")
    if theta["genre_drama"] > 0.2 and any("драма" in g.lower() for g in genres):
        genre_matches.append("драма")
    if theta["genre_crime"] > 0.2 and any("криминал" in g.lower() or "детектив" in g.lower() for g in genres):
        genre_matches.append("криминал")
    if theta["genre_horror"] > 0.2 and any("ужас" in g.lower() for g in genres):
        genre_matches.append("ужасы")
    if theta["genre_thriller"] > 0.2 and any("триллер" in g.lower() for g in genres):
        genre_matches.append("триллер")
    if theta["genre_romance"] > 0.2 and any("романтик" in g.lower() or "мелодрама" in g.lower() for g in genres):
        genre_matches.append("романтика")
    
    if genre_matches:
        bits.append(f"жанр: {', '.join(genre_matches)}")
    
    # Тип контента
    if theta["prefer_movies"] > 0.2 and "фильм" in content_type.lower():
        bits.append("фильм")
    elif theta["prefer_series"] > 0.2 and "сериал" in content_type.lower():
        bits.append("сериал")
    
    # Страна
    if theta["prefer_russian"] > 0.2 and any(c in country.lower() for c in ["россия", "рф", "советский"]):
        bits.append("российский")
    elif theta["prefer_foreign"] > 0.2 and not any(c in country.lower() for c in ["россия", "рф", "советский"]):
        bits.append("зарубежный")
    
    # Возрастной рейтинг
    age_rating = record_meta.get("age_rating")
    if theta["family_friendly"] > 0.2 and age_rating and age_rating <= 12:
        bits.append("семейный")
    elif theta["mature_content"] > 0.2 and age_rating and age_rating >= 16:
        bits.append("для взрослых")
    
    return " · ".join(bits[:3]) if bits else "совпадение по общим предпочтениям"

def filter_and_rank(df, embeddings, records_metadata, theta, model_kind, model, top_k=6):
    """Фильтрует и ранжирует рекомендации"""
    # Создаем текст запроса на основе профиля
    user_text = profile_keywords(theta)
    user_emb = embed_text(user_text, model_kind, model)
    
    # Вычисляем сходство
    sims = cosine_sim(user_emb, embeddings)
    
    # Создаем результирующий DataFrame
    res = df.copy()
    res["sim"] = sims
    res["score"] = sims.copy()
    
    # Применяем фильтры на основе метаданных
    for idx, record_meta in enumerate(records_metadata):
        if idx >= len(res):
            break
            
        bonus = 0.0
        
        # Фильтр по типу контента
        content_type = record_meta.get("content_type", "").lower()
        if theta["prefer_movies"] > 0.2 and "фильм" in content_type:
            bonus += 0.1
        elif theta["prefer_series"] > 0.2 and "сериал" in content_type:
            bonus += 0.1
        
        # Фильтр по стране
        country = record_meta.get("country", "").lower()
        if theta["prefer_russian"] > 0.2 and any(c in country for c in ["россия", "рф"]):
            bonus += 0.15
        elif theta["prefer_foreign"] > 0.2 and not any(c in country for c in ["россия", "рф"]):
            bonus += 0.1
        
        # Фильтр по возрастному рейтингу
        age_rating = record_meta.get("age_rating")
        if age_rating:
            if theta["family_friendly"] > 0.2 and age_rating <= 12:
                bonus += 0.1
            elif theta["mature_content"] > 0.2 and age_rating >= 16:
                bonus += 0.1
            elif theta["violence_tol"] < 0 and age_rating >= 18:
                bonus -= 0.2  # штраф за взрослый контент если не хотят насилие
        
        # Фильтр по жанрам
        genres = record_meta.get("genres", [])
        genre_bonus = 0.0
        for genre in genres:
            genre_lower = genre.lower()
            if theta["genre_comedy"] > 0.2 and "комедия" in genre_lower:
                genre_bonus += 0.1
            if theta["genre_drama"] > 0.2 and "драма" in genre_lower:
                genre_bonus += 0.1
            if theta["genre_action"] > 0.2 and ("боевик" in genre_lower or "экшн" in genre_lower):
                genre_bonus += 0.1
            if theta["genre_horror"] > 0.2 and "ужас" in genre_lower:
                genre_bonus += 0.1
            if theta["genre_thriller"] > 0.2 and "триллер" in genre_lower:
                genre_bonus += 0.1
            if theta["genre_romance"] > 0.2 and ("романтик" in genre_lower or "мелодрама" in genre_lower):
                genre_bonus += 0.1
        
        bonus += min(genre_bonus, 0.2)  # ограничиваем жанровый бонус
        
        res.iloc[idx, res.columns.get_loc("score")] += bonus
    
    # Сортируем и возвращаем топ результатов
    res = res.sort_values("score", ascending=False).head(top_k)
    return res

def init_theta():
    """Инициализирует профиль пользователя"""
    return {ax: 0.0 for ax in AXES}

def update_theta(theta, answer_value, targets):
    """Обновляет профиль пользователя на основе ответа"""
    s = answer_value / 2.0  # масштабируем к [-1..+1]
    for ax, weight in targets.items():
        theta[ax] = float(np.clip(theta[ax] + ETA * weight * s, -1.0, 1.0))

def pick_next_question(theta, asked_ids):
    """Выбирает следующий вопрос"""
    if len(asked_ids) >= QUESTIONS_MAX:
        return None
    
    remaining = [q for q in QUESTIONS if q["id"] not in asked_ids]
    if not remaining:
        return None
    
    def priority(q):
        unseen_axes = len(q["targets"])
        flatness = sum(1.0 - abs(theta.get(ax, 0.0)) for ax in q["targets"])
        return (unseen_axes, flatness)
    
    remaining.sort(key=priority, reverse=True)
    return remaining[0]

def main():
    """Основная функция"""
    print("\n=== Окконатор для Okko ===")
    print("Ответьте на несколько вопросов и получите подборку фильмов и сериалов с Okko.")
    print("В любой момент нажмите R — показать рекомендации, Q — выйти.\n")

    # Загружаем векторную БД Okko
    df, embeddings, metadata, records_metadata = load_okko_vector_db()
    
    if df is None:
        print("Не удалось загрузить данные Okko. Убедитесь, что векторная БД создана.")
        return
    
    # Загружаем модель
    model_kind, model = load_model()
    if model is None:
        print("Не удалось загрузить модель для эмбеддингов.")
        return

    theta = init_theta()
    asked = set()

    while True:
        # Проверяем лимит вопросов
        if len(asked) >= QUESTIONS_MAX:
            break

        q = pick_next_question(theta, asked)
        if q is None:
            break

        completeness = int(100 * len(asked) / QUESTIONS_MAX)
        print(f"\n[Уверенность профиля: {completeness}%]")
        print(f"Вопрос: {q['text']}")
        print("1) нет  2) скорее нет  3) не знаю  4) скорее да  5) да")
        ans = input("Ваш выбор (1-5, R — рекомендации, Q — выход): ").strip().upper()

        if ans == "Q":
            print("\nВыход.")
            sys.exit(0)
        if ans == "R":
            break
        if ans not in LIKERT:
            print("Некорректный ввод, пропускаю вопрос.")
            asked.add(q["id"])
            continue

        val = LIKERT[ans]
        if val != 0:
            update_theta(theta, val, q["targets"])
        asked.add(q["id"])

    print("\n=== Подборка для вас с Okko ===")
    recs = filter_and_rank(df, embeddings, records_metadata, theta, model_kind, model, top_k=6)
    
    if len(recs) == 0:
        print("Ничего не найдено. Попробуйте ответить на больше вопросов.")
    else:
        for i, (idx, row) in enumerate(recs.iterrows(), start=1):
            record_meta = records_metadata[idx] if idx < len(records_metadata) else {}
            
            title = safe_str(row["serial_name"])
            genres = ", ".join(record_meta.get("genres", []))
            content_type = record_meta.get("content_type", "")
            country = record_meta.get("country", "")
            age_rating = record_meta.get("age_rating")
            url = record_meta.get("url", "")
            
            age_str = f"{age_rating}+" if age_rating else "N/A"
            
            print(f"{i}. {title}")
            print(f"   Тип: {content_type} | Жанры: {genres}")
            print(f"   Страна: {country} | Возраст: {age_str}")
            
            why = explain_recommendation(row, theta, record_meta)
            if why:
                print(f"   Почему: {why}")
            
            if url:
                print(f"   Ссылка: {url}")
            print()
    
    print("Текущий профиль (значимые предпочтения):")
    for k, v in theta.items():
        if abs(v) > 0.1:
            print(f" - {k}: {v:+.2f}")

if __name__ == "__main__":
    main()
