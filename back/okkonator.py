import sys
import numpy as np
import pandas as pd
import json
import os

ETA = 0.3
QUESTIONS_MAX = 15
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Расширенные оси для всех параметров IMDB
AXES = [
    # Основные характеристики
    "tempo_slow", "darkness", "humor", "novelty", "length_short", "violence_tol",
    
    # Жанры
    "genre_action", "genre_comedy", "genre_drama", "genre_crime", "genre_scifi",
    "genre_horror", "genre_thriller", "genre_romance", "genre_fantasy", "genre_animation",
    "genre_biography", "genre_history", "genre_mystery", "genre_adventure", "genre_sport",
    
    # Качество и популярность
    "high_rating", "popular", "recent", "classic",
    
    # Специфические предпочтения
    "animation_pref", "biography_pref", "historical_pref"
]

QUESTIONS = [
    # Основные предпочтения
    {"id":"q1", "text":"Сейчас хочется чего-то лёгкого и тёплого?",
     "targets":{"darkness":-1, "humor":+1}},
    {"id":"q2", "text":"Окей медленный, атмосферный темп?",
     "targets":{"tempo_slow":+1}},
    {"id":"q3", "text":"Юмор обязателен сегодня?",
     "targets":{"humor":+1, "genre_comedy":+1}},
    {"id":"q4", "text":"Мрачные/тяжёлые темы — нормально?",
     "targets":{"darkness":+1}},
    {"id":"q5", "text":"Хочется короткого (до ~110 минут)?",
     "targets":{"length_short":+1}},
    {"id":"q6", "text":"Готовы к нестандартному/экспериментальному?",
     "targets":{"novelty":+1}},
    {"id":"q7", "text":"Окей с жёсткими сценами (насилие)?",
     "targets":{"violence_tol":+1}},
    
    # Жанровые предпочтения
    {"id":"q8", "text":"Тянет к экшну и приключениям?",
     "targets":{"genre_action":+1, "genre_adventure":+1}},
    {"id":"q9", "text":"Криминал/детектив интереснее фантастики?",
     "targets":{"genre_crime":+1, "genre_scifi":-1}},
    {"id":"q10","text":"Хочется ужастик или триллер?",
     "targets":{"genre_horror":+1, "genre_thriller":+1}},
    {"id":"q11","text":"Романтика тоже подойдёт?",
     "targets":{"genre_romance":+1}},
    {"id":"q12","text":"Фэнтези или анимация интересны?",
     "targets":{"genre_fantasy":+1, "genre_animation":+1, "animation_pref":+1}},
    {"id":"q13","text":"Биографические фильмы привлекают?",
     "targets":{"genre_biography":+1, "biography_pref":+1}},
    {"id":"q14","text":"Исторические фильмы интересны?",
     "targets":{"genre_history":+1, "historical_pref":+1}},
    {"id":"q15","text":"Хочется что-то с высоким рейтингом?",
     "targets":{"high_rating":+1}},
    {"id":"q16","text":"Предпочитаете популярные фильмы?",
     "targets":{"popular":+1}},
    {"id":"q17","text":"Свежие фильмы (после 2015) или классика?",
     "targets":{"recent":+1, "classic":-1}},
]

LIKERT = {
    "1": -2,   # нет
    "2": -1,   # скорее нет
    "3":  0,   # не знаю
    "4":  1,   # скорее да
    "5":  2,   # да
}

def load_vector_db(data_dir="../data"):
    """Загружает предварительно созданную векторную базу данных"""
    try:
        df = pd.read_pickle(f"{data_dir}/movies_df.pkl")
        embeddings = np.load(f"{data_dir}/embeddings.npy")
        
        with open(f"{data_dir}/metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        print(f"Загружена векторная БД: {len(df)} фильмов")
        return df, embeddings, metadata
    except FileNotFoundError:
        print("Векторная БД не найдена. Запустите analyze_and_build_db.py сначала.")
        return None, None, None

def load_movies_fallback(path="../data/IMBD.csv"):
    """Загружает фильмы напрямую из CSV (fallback)"""
    df = pd.read_csv(path)
    
    # Очистка и обработка данных IMDB
    df["genre"] = df["genre"].fillna("")
    df["description"] = df["description"].fillna("")
    
    # Извлечение года из поля year (может содержать диапазоны типа "2018– ")
    df["year"] = df["year"].str.extract(r'(\d{4})').astype(float)
    df["year"] = df["year"].fillna(2020)  # дефолт для неизвестных годов
    
    # Обработка duration (убираем " min" и конвертируем в минуты)
    df["duration"] = df["duration"].str.replace(" min", "").str.replace(" min", "")
    df["duration"] = pd.to_numeric(df["duration"], errors='coerce')
    df["duration"] = df["duration"].fillna(90)  # дефолт 90 минут
    
    # Обработка rating
    df["rating"] = pd.to_numeric(df["rating"], errors='coerce')
    df["rating"] = df["rating"].fillna(6.0)  # дефолт 6.0
    
    # Обработка votes
    df["votes"] = df["votes"].str.replace(",", "").astype(float)
    df["votes"] = df["votes"].fillna(1000)
    
    # Создание поля violence на основе certificate и genre
    violence_keywords = ["R", "TV-MA", "NC-17"]
    violence_genres = ["Horror", "Thriller", "Crime", "Action"]
    df["violence"] = 0
    df.loc[df["certificate"].isin(violence_keywords), "violence"] = 1
    df.loc[df["genre"].str.contains("|".join(violence_genres), case=False, na=False), "violence"] = 1
    
    return df

def try_load_model():
    # Пытаемся sentence-transformers; если не вышло — TF-IDF
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(MODEL_NAME)
        return ("st", model)
    except Exception as e:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=5000)
        return ("tfidf", vec)

def build_item_embeddings(df, model_kind, model):
    texts = (df["title"].fillna("") + " " +
             df["description"].fillna("") + " " +
             df["genre"].fillna(""))
    if model_kind == "st":
        X = model.encode(texts.tolist(), normalize_embeddings=True)
        return X
    else:
        X = model.fit_transform(texts.tolist()).astype(np.float32)
        A = X.toarray()
        norms = np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
        return A / norms

def embed_text(text, model_kind, model):
    if model_kind == "st":
        v = model.encode([text], normalize_embeddings=True)[0]
        return v
    else:
        X = model.transform([text]).astype(np.float32).toarray()[0]
        v = X / (np.linalg.norm(X) + 1e-9)
        return v

def cosine_sim(a, B):
    return (B @ a) / (np.linalg.norm(a)+1e-9)

def profile_keywords(theta):
    t = theta
    tokens = []
    
    # Основные характеристики
    if t["tempo_slow"] > 0.2: tokens += ["slow-burn","atmospheric","character-driven"]
    if t["darkness"] > 0.2: tokens += ["dark","gritty","noir"]
    if t["darkness"] < -0.2: tokens += ["warm","feel-good","cozy"]
    if t["humor"] > 0.2: tokens += ["funny","comedy","lighthearted"]
    if t["novelty"] > 0.2: tokens += ["unconventional","experimental","fresh"]
    
    # Жанры
    if t["genre_action"] > 0.2: tokens += ["action","adventure","thrilling"]
    if t["genre_comedy"] > 0.2: tokens += ["comedy","funny","humorous"]
    if t["genre_drama"] > 0.2: tokens += ["drama","emotional","serious"]
    if t["genre_crime"] > 0.2: tokens += ["crime","detective","mystery"]
    if t["genre_scifi"] > 0.2: tokens += ["sci-fi","science fiction","futuristic"]
    if t["genre_horror"] > 0.2: tokens += ["horror","scary","frightening"]
    if t["genre_thriller"] > 0.2: tokens += ["thriller","suspense","tense"]
    if t["genre_romance"] > 0.2: tokens += ["romance","love","romantic"]
    if t["genre_fantasy"] > 0.2: tokens += ["fantasy","magical","supernatural"]
    if t["genre_animation"] > 0.2: tokens += ["animation","animated","cartoon"]
    if t["genre_biography"] > 0.2: tokens += ["biography","biographical","real life"]
    if t["genre_history"] > 0.2: tokens += ["historical","history","period"]
    if t["genre_mystery"] > 0.2: tokens += ["mystery","puzzle","enigma"]
    if t["genre_adventure"] > 0.2: tokens += ["adventure","exploration","journey"]
    if t["genre_sport"] > 0.2: tokens += ["sport","sports","athletic"]
    
    # Качество и популярность
    if t["high_rating"] > 0.2: tokens += ["high-rated","critically acclaimed","award-winning"]
    if t["popular"] > 0.2: tokens += ["popular","mainstream","blockbuster"]
    if t["recent"] > 0.2: tokens += ["recent","modern","contemporary"]
    if t["classic"] > 0.2: tokens += ["classic","timeless","vintage"]
    
    if not tokens:
        tokens = ["balanced","popular","well-rated"]
    return " ".join(tokens)

def explain(row, theta):
    bits = []
    genre_str = str(row["genre"]).lower()
    
    # Основные характеристики
    if theta["tempo_slow"] > 0.2: bits.append("медленный/атмосферный темп")
    if theta["darkness"] > 0.2: bits.append("мрачный вайб")
    if theta["darkness"] < -0.2: bits.append("тёплый/лайтовый вайб")
    if theta["humor"] > 0.2 and "comedy" in genre_str: bits.append("хотели юмор — это комедия")
    if theta["length_short"] > 0.2 and row["duration"] <= 110: bits.append("короткий (≤110 мин)")
    if theta["novelty"] > 0.2 and row["year"] >= 2015: bits.append("свежее")
    
    # Жанры
    if theta["genre_action"] > 0.2 and "action" in genre_str: bits.append("экшн")
    if theta["genre_comedy"] > 0.2 and "comedy" in genre_str: bits.append("комедия")
    if theta["genre_drama"] > 0.2 and "drama" in genre_str: bits.append("драма")
    if theta["genre_crime"] > 0.2 and "crime" in genre_str: bits.append("криминал/детектив")
    if theta["genre_scifi"] > 0.2 and "sci-fi" in genre_str: bits.append("sci-fi")
    if theta["genre_horror"] > 0.2 and "horror" in genre_str: bits.append("ужасы")
    if theta["genre_thriller"] > 0.2 and "thriller" in genre_str: bits.append("триллер")
    if theta["genre_romance"] > 0.2 and "romance" in genre_str: bits.append("романтика")
    if theta["genre_fantasy"] > 0.2 and "fantasy" in genre_str: bits.append("фэнтези")
    if theta["genre_animation"] > 0.2 and "animation" in genre_str: bits.append("анимация")
    if theta["genre_biography"] > 0.2 and "biography" in genre_str: bits.append("биография")
    if theta["genre_history"] > 0.2 and "history" in genre_str: bits.append("исторический")
    if theta["genre_mystery"] > 0.2 and "mystery" in genre_str: bits.append("мистика")
    if theta["genre_adventure"] > 0.2 and "adventure" in genre_str: bits.append("приключения")
    if theta["genre_sport"] > 0.2 and "sport" in genre_str: bits.append("спорт")
    
    # Качество и популярность
    if theta["high_rating"] > 0.2 and row["rating"] >= 8.0: bits.append("высокий рейтинг")
    if theta["popular"] > 0.2 and row["votes"] >= 100000: bits.append("популярный")
    if theta["recent"] > 0.2 and row["year"] >= 2015: bits.append("современный")
    if theta["classic"] > 0.2 and row["year"] < 2010: bits.append("классика")
    
    return " · ".join(bits[:3]) if bits else "совпадение по общему вкусу"

def filter_and_rank(df, ITEM_EMB, theta, model_kind, model, top_k=6):
    user_text = profile_keywords(theta)
    user_emb = embed_text(user_text, model_kind, model)
    sims = cosine_sim(user_emb, ITEM_EMB)
    res = df.copy()
    res["sim"] = sims

    # Жёсткие фильтры
    if theta["violence_tol"] < 0:
        res = res[res["violence"] == 0]

    # Мягкие фильтры
    res["length_penalty"] = 0.0
    res["year_bonus"] = 0.0
    res["rating_bonus"] = 0.0
    res["popularity_bonus"] = 0.0

    # Длина
    if theta["length_short"] > 0.2:
        res["length_penalty"] = np.where(res["duration"] <= 110, 0.0, -0.1)

    # Новизна/классика
    if len(res) > 0:
        year_min, year_max = res["year"].min(), res["year"].max()
        rng = max(1, year_max - year_min)
        if theta["recent"] > 0.2:
            res["year_bonus"] = 0.05 * ((res["year"] - year_min) / rng)
        elif theta["classic"] > 0.2:
            res["year_bonus"] = -0.05 * ((res["year"] - year_min) / rng)
        elif theta["novelty"] > 0.2:
            res["year_bonus"] = 0.03 * ((res["year"] - year_min) / rng)

    # Рейтинг
    if theta["high_rating"] > 0.2:
        res["rating_bonus"] = 0.1 * (res["rating"] - 6.0) / 4.0  # нормализация 6-10

    # Популярность
    if theta["popular"] > 0.2:
        votes_log = np.log10(res["votes"] + 1)
        votes_max = votes_log.max()
        if votes_max > 0:
            res["popularity_bonus"] = 0.05 * (votes_log / votes_max)

    res["score"] = (res["sim"] + res["length_penalty"] + 
                   res["year_bonus"] + res["rating_bonus"] + res["popularity_bonus"])
    res = res.sort_values("score", ascending=False).head(top_k)
    return res

def init_theta():
    return {ax: 0.0 for ax in AXES}

def update_theta(theta, answer_value, targets):
    s = answer_value / 2.0  # scale to [-1..+1]
    for ax, weight in targets.items():
        theta[ax] = float(np.clip(theta[ax] + ETA * weight * s, -1.0, 1.0))

def pick_next_question(theta, asked_ids):
    remaining = [q for q in QUESTIONS if q["id"] not in asked_ids]
    if not remaining:
        return None
    def prio(q):
        unseen_axes = len(q["targets"])
        flatness = sum(1.0 - abs(theta.get(ax,0.0)) for ax in q["targets"])
        return (unseen_axes, flatness)
    remaining.sort(key=prio, reverse=True)
    return remaining[0]

def main():
    print("\n=== Окконатор (расширенный) ===")
    print("Ответьте на несколько вопросов и получите подборку фильмов.")
    print("В любой момент нажмите R — показать рекомендации, Q — выйти.\n")

    # Попытка загрузить векторную БД
    df, ITEM_EMB, metadata = load_vector_db()
    
    if df is None:
        print("Загружаем данные напрямую из CSV...")
        df = load_movies_fallback()
        model_kind, model = try_load_model()
        ITEM_EMB = build_item_embeddings(df, model_kind, model)
    else:
        print("Используем предварительно созданную векторную БД")
        model_kind, model = try_load_model()

    theta = init_theta()
    asked = set()

    while True:
        # стоп по количеству вопросов
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

    print("\n=== Подборка для вас ===")
    recs = filter_and_rank(df, ITEM_EMB, theta, model_kind, model, top_k=6)
    if len(recs) == 0:
        print("Ничего не найдено. Ослабьте ограничения и попробуйте снова.")
    else:
        for i, (_, row) in enumerate(recs.iterrows(), start=1):
            why = explain(row, theta)
            votes_str = f"{int(row['votes']):,}" if 'votes' in row else "N/A"
            print(f"{i}. {row['title']}  | Жанры: {row['genre']} | {int(row['duration'])} мин | {int(row['year'])} | Рейтинг: {row['rating']:.1f} | Голосов: {votes_str}")
            if why:
                print(f"   Почему: {why}")
    
    print("\nТекущий профиль (оси):")
    for k,v in theta.items():
        if abs(v) > 0.1:  # показываем только значимые значения
            print(f" - {k}: {v:+.2f}")

if __name__ == "__main__":
    main()
