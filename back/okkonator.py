import os
import json
import numpy as np
import pandas as pd
import streamlit as st

# ====== Настройки ======
ETA = 0.3                 # скорость обучения профиля
QUESTIONS_MAX = 10        # максимум вопросов (короткий режим)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384-d

# ====== Данные ======
@st.cache_data
def load_movies():
    df = pd.read_csv("movies.csv")
    df["genres_list"] = df["genres"].fillna("").apply(lambda x: [g.strip() for g in x.split(";") if g.strip()])
    return df

movies = load_movies()

# ====== Модель эмбеддингов ======
@st.cache_resource
def load_model():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(MODEL_NAME), "st"
    except Exception as e:
        st.warning("Не удалось загрузить sentence-transformers, переключаюсь на TF-IDF (качество ниже).")
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=5000)
        return vec, "tfidf"

model, model_kind = load_model()

@st.cache_resource
def embed_items(df):
    texts = (df["title"].fillna("") + " " +
             df["overview"].fillna("") + " " +
             df["genres"].fillna(""))
    if model_kind == "st":
        X = model.encode(texts.tolist(), normalize_embeddings=True)
    else:
        X = model.fit_transform(texts.tolist()).astype(np.float32)
        # нормализуем
        norms = np.linalg.norm(X.toarray(), axis=1, keepdims=True) + 1e-9
        X = X.toarray() / norms
    return X

ITEM_EMB = embed_items(movies)

# ====== Оси профиля (10 шт.) ======
AXES = [
    "tempo_slow",         # медленный/атмосферный
    "darkness",           # мрачность/нуар
    "humor",              # юмор
    "novelty",            # новизна (новинки vs классика)
    "length_short",       # короткое (<=110 мин)
    "violence_tol",       # толерантность к жестким сценам
    "genre_crime",
    "genre_comedy",
    "genre_scifi",
    "genre_drama",
]

# ====== Вопросы: каждый бьет по нескольким осям ======
# Ответ: -2, -1, 0, +1, +2
QUESTIONS = [
    {"id":"q1", "text":"Сейчас хочется чего-то лёгкого и тёплого?",
     "targets":{"darkness":-1, "humor":+1}},
    {"id":"q2", "text":"Окей медленный, атмосферный темп?",
     "targets":{"tempo_slow":+1}},
    {"id":"q3", "text":"Юмор обязателен сегодня?",
     "targets":{"humor":+1}},
    {"id":"q4", "text":"Мрачные/тяжёлые темы — нормально?",
     "targets":{"darkness":+1}},
    {"id":"q5", "text":"Хочется короткого (до ~110 минут)?",
     "targets":{"length_short":+1}},
    {"id":"q6", "text":"Готовы к нестандартному/экспериментальному?",
     "targets":{"novelty":+1}},
    {"id":"q7", "text":"Окей с жёсткими сценами (насилие)?",
     "targets":{"violence_tol":+1}},
    {"id":"q8", "text":"Тянет больше к криминалу/детективу, чем к фантастике?",
     "targets":{"genre_crime":+1, "genre_scifi":-1}},
    {"id":"q9", "text":"Комедия тоже подойдёт?",
     "targets":{"genre_comedy":+1}},
    {"id":"q10","text":"Готовы к серьёзной драме?",
     "targets":{"genre_drama":+1}},
]

LIKERT_LABELS = ["нет (-2)","скорее нет (-1)","не знаю (0)","скорее да (+1)","да (+2)"]
LIKERT_VALUES = [-2,-1,0,1,2]

# ====== Вспомогалки ======
def init_state():
    if "theta" not in st.session_state:
        st.session_state.theta = {ax: 0.0 for ax in AXES}
    if "asked" not in st.session_state:
        st.session_state.asked = set()
    if "answers" not in st.session_state:
        st.session_state.answers = {}

def update_theta(answer_value, targets):
    # answer_value ∈ {-2..+2} -> scale to [-1..+1]
    s = answer_value / 2.0
    for ax, weight in targets.items():
        # weight ∈ {-1..+1}: направление оси
        st.session_state.theta[ax] = float(np.clip(
            st.session_state.theta[ax] + ETA * weight * s, -1.0, 1.0
        ))

def profile_keywords(theta):
    # Простая генерация "профильного текста" из осей
    tokens = []
    if theta["tempo_slow"] > 0.2: tokens += ["slow-burn","atmospheric","character-driven"]
    if theta["darkness"] > 0.2: tokens += ["dark","gritty","noir"]
    if theta["darkness"] < -0.2: tokens += ["warm","feel-good","cozy"]
    if theta["humor"] > 0.2: tokens += ["funny","comedy","lighthearted"]
    if theta["novelty"] > 0.2: tokens += ["unconventional","experimental","fresh"]
    if theta["genre_crime"] > 0.2: tokens += ["crime","detective","mystery"]
    if theta["genre_comedy"] > 0.2: tokens += ["comedy"]
    if theta["genre_scifi"] > 0.2: tokens += ["sci-fi","science fiction","futuristic"]
    if theta["genre_drama"] > 0.2: tokens += ["drama","emotional"]
    # длина/насилие — как фильтры, не в текст
    if not tokens:
        tokens = ["balanced","popular","well-rated"]
    return " ".join(tokens)

def embed_text(text):
    if model_kind == "st":
        emb = model.encode([text], normalize_embeddings=True)[0]
    else:
        X = model.transform([text]).astype(np.float32)
        v = X.toarray()[0]
        emb = v / (np.linalg.norm(v)+1e-9)
    return emb

def cosine_sim(a, B):
    # a: (d,), B: (n,d)
    return (B @ a) / (np.linalg.norm(a)+1e-9)

def filter_and_rank(theta, top_k=10):
    user_text = profile_keywords(theta)
    user_emb = embed_text(user_text)
    sims = cosine_sim(user_emb, ITEM_EMB)

    df = movies.copy()
    df["sim"] = sims

    # Жёсткие фильтры
    if theta["violence_tol"] < 0:    # против жёстких сцен
        df = df[df["violence"] == 0]
    if theta["length_short"] > 0.2:  # предпочитаем <=110
        df["length_penalty"] = np.where(df["runtime"] <= 110, 0.0, -0.1)
    else:
        df["length_penalty"] = 0.0

    # Мягкий бонус за новизну/классику
    year_bonus = 0.0
    if theta["novelty"] > 0.2:
        year_bonus = 0.05 * ((df["year"] - df["year"].min()) / (df["year"].max()-df["year"].min()+1e-9))
    elif theta["novelty"] < -0.2:
        year_bonus = -0.05 * ((df["year"] - df["year"].min()) / (df["year"].max()-df["year"].min()+1e-9))
    df["score"] = df["sim"] + df["length_penalty"] + year_bonus

    recs = df.sort_values("score", ascending=False).head(top_k)
    return recs[["id","title","genres","runtime","year","score"]]

def explain_card(row, theta):
    bits = []
    if theta["tempo_slow"] > 0.2: bits.append("медленный/атмосферный темп")
    if theta["darkness"] > 0.2: bits.append("мрачный вайб")
    if theta["darkness"] < -0.2: bits.append("тёплый/лайтовый вайб")
    if theta["humor"] > 0.2 and "Comedy" in row["genres"]: bits.append("хотели юмор — это комедия")
    if theta["length_short"] > 0.2 and row["runtime"] <= 110: bits.append("короткий (≤110 мин)")
    if theta["genre_crime"] > 0.2 and "Crime" in row["genres"]: bits.append("криминал/детектив")
    if theta["genre_scifi"] > 0.2 and "Sci-Fi" in row["genres"]: bits.append("sci-fi")
    if theta["genre_drama"] > 0.2 and "Drama" in row["genres"]: bits.append("драма")
    if theta["novelty"] > 0.2 and row["year"] >= 2015: bits.append("свежее")
    return " · ".join(bits[:3]) if bits else "совпадение по общему вкусу"

def next_question():
    # берём первый не заданный; чуть-чуть умнее — приоритет тем,
    # где theta ближе к 0 и которых ещё не трогали.
    remaining = [q for q in QUESTIONS if q["id"] not in st.session_state.asked]
    if not remaining:
        return None
    # примитивный приоритет: сколько новых осей затрагивает вопрос
    def prio(q):
        unseen_axes = sum(1 for ax in q["targets"].keys())
        flatness = sum(1.0 - abs(st.session_state.theta.get(ax, 0.0)) for ax in q["targets"].keys())
        return (unseen_axes, flatness)
    remaining.sort(key=prio, reverse=True)
    return remaining[0]

# ====== UI ======
st.set_page_config(page_title="Окконатор (минимал)", page_icon="🎬", layout="centered")
st.title("🎬 Окконатор — быстрая настройка вкуса")

init_state()

col1, col2 = st.columns([3,2])
with col1:
    st.markdown("Ответьте на несколько вопросов — получим базовый профиль и покажем подборку.")
with col2:
    completeness = int(100 * len(st.session_state.asked) / QUESTIONS_MAX)
    st.progress(min(completeness,100), text=f"Уверенность профиля: {completeness}%")

q = next_question()
if q and len(st.session_state.asked) < QUESTIONS_MAX:
    st.subheader(q["text"])
    choice = st.radio("Ваш ответ:", LIKERT_LABELS, index=2, horizontal=True, key=f"ans_{q['id']}")
    btns = st.columns(2)
    if btns[0].button("Следующий вопрос"):
        val = LIKERT_VALUES[LIKERT_LABELS.index(choice)]
        if val != 0:  # "не знаю" = 0 → не обновляем
            update_theta(val, q["targets"])
        st.session_state.asked.add(q["id"])
        st.rerun()
    show_now = btns[1].button("Показать подборку сейчас")
else:
    show_now = True

st.divider()

if show_now:
    st.subheader("Подборка для вас")
    recs = filter_and_rank(st.session_state.theta, top_k=6)
    for _, row in recs.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['title']}**  \nЖанры: {row['genres']} · {int(row['runtime'])} мин · {int(row['year'])}")
            st.caption(explain_card(row, st.session_state.theta))

st.divider()
with st.expander("Посмотреть текущий профиль (θ)"):
    st.json(st.session_state.theta)
