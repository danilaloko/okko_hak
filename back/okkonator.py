# okkonator.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import math
import uuid

# -----------------------------
# Константы и утилиты
# -----------------------------
LIKERT_MAP: Dict[str, int] = {
    # RU
    "совсем нет": -2, "нет": -2,
    "скорее нет": -1,
    "не знаю": 0, "пропустить": 0, "скип": 0, "skip": 0,
    "скорее да": 1,
    "да": 2,
    # EN
    "strongly disagree": -2, "disagree": -2,
    "rather no": -1, "somewhat no": -1,
    "neutral": 0, "idk": 0, "unknown": 0, "n/a": 0,
    "rather yes": 1, "somewhat yes": 1,
    "agree": 2, "strongly agree": 2,
}
LIKERT_OPTIONS = ["Совсем нет", "Скорее нет", "Не знаю", "Скорее да", "Да"]

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def l2norm(weights: Dict[str, float]) -> float:
    return math.sqrt(sum(v*v for v in weights.values()))

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """L2-нормализация весов вопроса, чтобы вклад по осям был сопоставим."""
    n = l2norm(weights)
    if n == 0:
        return weights.copy()
    return {k: v/n for k, v in weights.items()}

# -----------------------------
# Модель состояния
# -----------------------------
@dataclass
class AxisState:
    """Состояние одной скрытой оси предпочтений: среднее (mu) и неопределённость (sigma)."""
    mu: float = 0.0           # текущая оценка предпочтения [-1..1], 0 = неизвестно/нейтрально
    sigma: float = 1.0        # неопределённость [sigma_min..sigma_max]; меньше = увереннее

@dataclass
class Question:
    id: str
    text: str
    # Веса влияния вопроса на оси (положительные = "да" толкает mu вверх по оси)
    weights: Dict[str, float]

@dataclass
class OkkonatorConfig:
    axes: List[str]
    questions: List[Question]
    q_max: int = 16                # максимум вопросов в сессии
    sigma_min: float = 0.15        # нижняя граница неопределённости
    sigma_max: float = 1.00        # верхняя граница неопределённости (стартовое значение)
    base_lr: float = 0.60          # базовая "скорость обучения" (для сходимости)
    entropy_target: float = 0.35   # целевая средняя неопределённость (ниже — стоп)
    coverage_lambda: float = 0.10  # штраф за "переспрашивание" уже тронутых осей

@dataclass
class OkkonatorSession:
    """Хранит всё состояние сессии: оси, история, уже заданные вопросы."""
    session_id: str
    axes_state: Dict[str, AxisState]
    asked_ids: List[str] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)  # [{question_id, answer_raw, answer_num, before, after}]

# -----------------------------
# Движок Окконатора
# -----------------------------
class OkkonatorEngine:
    def __init__(self, config: Optional[OkkonatorConfig] = None):
        if config is None:
            config = self._default_config()
        self.config = config
        self.session = self._new_session()

    # --------- Публичное API ---------
    def reset(self) -> None:
        self.session = self._new_session()

    def start(self) -> Dict[str, Any]:
        """Вернёт первый вопрос и текущую уверенность (обычно низкая)."""
        next_q = self._select_next_question()
        return self._response(next_q)

    def step(self, question_id: str, answer: Any) -> Dict[str, Any]:
        """
        Обрабатывает ответ на предыдущий вопрос и возвращает:
        - confidence_pct: процент уверенности (0..100)
        - next_question: {id, text, options} либо None (если готово)
        - complete: bool (достигнут порог уверенности или лимит вопросов)
        """
        # 1) Преобразуем ответ
        ans_num = self._normalize_answer(answer)  # int в [-2..2]
        # 2) Найдём вопрос и применим апдейт
        question = self._get_question(question_id)
        if question is None:
            raise ValueError(f"Unknown question_id: {question_id}")

        before_snapshot = self._axes_snapshot()
        self._apply_update(question, ans_num)
        after_snapshot = self._axes_snapshot()

        # 3) Лог
        self.session.history.append({
            "question_id": question_id,
            "answer_raw": answer,
            "answer_num": ans_num,
            "before": before_snapshot,
            "after": after_snapshot,
        })
        if question_id not in self.session.asked_ids:
            self.session.asked_ids.append(question_id)

        # 4) Вычислим следующую рекомендацию/вопрос
        complete = self._is_complete()
        next_q = None if complete else self._select_next_question()
        return self._response(next_q, complete=complete)

    # --------- Внутреннее ---------
    def _new_session(self) -> OkkonatorSession:
        axes_state = {ax: AxisState(mu=0.0, sigma=self.config.sigma_max) for ax in self.config.axes}
        return OkkonatorSession(session_id=str(uuid.uuid4()), axes_state=axes_state)

    def _axes_snapshot(self) -> Dict[str, Tuple[float, float]]:
        return {ax: (state.mu, state.sigma) for ax, state in self.session.axes_state.items()}

    def _normalize_answer(self, answer: Any) -> int:
        """
        Поддерживает:
        - уже числовые значения: -2,-1,0,1,2
        - строковые: см. LIKERT_MAP
        """
        if isinstance(answer, int):
            if answer < -2 or answer > 2:
                raise ValueError("Numeric answer must be in [-2..2]")
            return answer
        if isinstance(answer, float):
            # округлим к ближайшему допустимому
            r = int(round(clamp(answer, -2.0, 2.0)))
            return r
        if isinstance(answer, str):
            key = answer.strip().lower()
            if key in LIKERT_MAP:
                return LIKERT_MAP[key]
            # Попытка прочитать +/-2 из текстов "да/нет" без точного совпадения
            if key in {"y", "yes", "да!", "да.)", "ага"}:
                return 2
            if key in {"n", "no", "нет", "неа"}:
                return -2
            if key in {"?", "не уверен", "неуверен", "maybe", "может быть"}:
                return 0
        raise ValueError(f"Unsupported answer format: {answer!r}")

    def _get_question(self, question_id: str) -> Optional[Question]:
        for q in self.config.questions:
            if q.id == question_id:
                return q
        return None

    def _apply_update(self, q: Question, ans_num: int) -> None:
        """
        Локально-байесовская линейная корректировка по осям:
        - прогноз ответа = sum(w_j * mu_j)
        - ошибка = (ans_norm - прогноз)
        - обновление mu_j += kappa * w_j * ошибка
        - уменьшение sigma_j пропорционально |w_j| и |ans_norm|
        """
        if not q.weights:
            return
        # нормализуем веса вопроса
        w = normalize_weights(q.weights)

        # Нормированный ответ [-1,1]
        ans_norm = ans_num / 2.0  # -1..1

        # Прогноз по текущему состоянию
        pred = sum(w_ax * self.session.axes_state[ax].mu for ax, w_ax in w.items())

        # Ошибка модели
        err = ans_norm - pred

        # Адаптивная скорость обучения по неопределённости затронутых осей
        sigmas = [self.session.axes_state[ax].sigma for ax in w.keys()]
        avg_sigma = sum(sigmas) / (len(sigmas) or 1)
        kappa = self.config.base_lr * (0.5 + 0.5 * (avg_sigma - self.config.sigma_min) / (self.config.sigma_max - self.config.sigma_min))
        kappa = clamp(kappa, 0.15, 0.95)

        # Обновляем каждую ось
        for ax, w_ax in w.items():
            st = self.session.axes_state[ax]
            # апдейт среднего
            st.mu = clamp(st.mu + kappa * w_ax * err, -1.0, 1.0)
            # апдейт неопределённости (чем информативнее ответ — тем сильнее уверенность)
            shrink = 0.25 * abs(w_ax) * abs(ans_norm)  # 0..0.25
            st.sigma = clamp(st.sigma * (1.0 - shrink), self.config.sigma_min, self.config.sigma_max)

        # Доп. небольшое «затухание» неопределённости для прочих осей (раз мы задавали вопрос вообще)
        for ax, st in self.session.axes_state.items():
            if ax not in w:
                st.sigma = clamp(st.sigma * 0.995, self.config.sigma_min, self.config.sigma_max)

    def _avg_sigma(self) -> float:
        return sum(st.sigma for st in self.session.axes_state.values()) / len(self.session.axes_state)

    def _confidence_pct(self) -> float:
        """
        Переводим среднюю неопределённость в 0..100%.
        sigma_max -> 0%, sigma_min -> 100%
        Плюс лёгкий бонус за прогресс по числу вопросов.
        """
        avg_sigma = self._avg_sigma()
        rng = self.config.sigma_max - self.config.sigma_min
        if rng <= 1e-9:
            base = 100.0
        else:
            base = 100.0 * (self.config.sigma_max - avg_sigma) / rng
        # бонус за долю пройденных вопросов (до +10 п.п.)
        q_bonus = 10.0 * (len(self.session.asked_ids) / max(1, self.config.q_max))
        return clamp(base + q_bonus, 0.0, 100.0)

    def _is_complete(self) -> bool:
        # 1) достигли лимит вопросов
        if len(self.session.asked_ids) >= self.config.q_max:
            return True
        # 2) упали ниже целевой неопределённости
        if self._avg_sigma() <= self.config.entropy_target:
            return True
        return False

    def _select_next_question(self) -> Optional[Question]:
        """Выбирает вопрос, который максимально уменьшит неопределённость (на глазок)."""
        candidates = [q for q in self.config.questions if q.id not in self.session.asked_ids]
        if not candidates:
            return None

        # Оценка "инфо-гейна": сумма |w| * sigma по осям, минус небольшой штраф за перекрытие уже часто тронутых осей
        # Частота затронутости осей ранее
        axis_touch_count: Dict[str, int] = {ax: 0 for ax in self.config.axes}
        for qid in self.session.asked_ids:
            qq = self._get_question(qid)
            if not qq:
                continue
            for ax in qq.weights.keys():
                axis_touch_count[ax] += 1

        best_q: Optional[Question] = None
        best_score: float = -1e9

        for q in candidates:
            w_norm = normalize_weights(q.weights)
            gain = 0.0
            penalty = 0.0
            for ax, w_ax in w_norm.items():
                sigma = self.session.axes_state[ax].sigma
                gain += abs(w_ax) * sigma
                penalty += self.config.coverage_lambda * axis_touch_count.get(ax, 0) * abs(w_ax)
            score = gain - penalty
            if score > best_score:
                best_score = score
                best_q = q

        return best_q

    def _response(self, next_q: Optional[Question], complete: Optional[bool] = None) -> Dict[str, Any]:
        if complete is None:
            complete = self._is_complete()
        payload = {
            "session_id": self.session.session_id,
            "confidence_pct": round(self._confidence_pct(), 1),
            "complete": complete,
            "next_question": None if (complete or next_q is None) else {
                "id": next_q.id,
                "text": next_q.text,
                "options": LIKERT_OPTIONS
            },
            # можно отдать наружу краткий срез состояния (по желанию фронта)
            "profile_preview": self.profile_preview(),
        }
        return payload

    def profile_preview(self, top_k: int = 6) -> List[Tuple[str, float]]:
        """Топ осей по абсолютному выраженному предпочтению (|mu|), для отображения и отладки."""
        pairs = sorted(((ax, st.mu) for ax, st in self.session.axes_state.items()),
                       key=lambda t: abs(t[1]), reverse=True)
        return pairs[:top_k]

    # -----------------------------
    # Конфигурация по умолчанию
    # -----------------------------
    def _default_config(self) -> OkkonatorConfig:
        axes = [
            "valence",          # тёплое/радостное (+) ↔ печаль/тяжесть (−)
            "arousal",          # спокойное (−) ↔ динамичное/энергичное (+)
            "tempo",            # медленное (−) ↔ быстрое (+)
            "darkness",         # мрачность/нуар (+)
            "humor",            # важность юмора (+)
            "violence_ok",      # терпимость к жестким сценам (+)
            "novelty",          # готовность к экспериментам/новинкам (+)
            "runtime_short",    # предпочтение ≤ ~50–60 мин (+)
            "non_english_ok",   # ок с не-англоязычным (+)
            "crime_pref",       # тянет к криминалу/детективу (+)
            "scifi_pref",       # тянет к фантастике (+)
            "romcom_pref",      # тянет к романтической комедии (+)
            "doc_pref",         # ок с документалистикой (+)
        ]
        q = []
        def add(qid: str, text: str, w: Dict[str, float]):
            q.append(Question(qid, text, w))

        add("q1", "Сейчас хочется чего-то лёгкого и тёплого?", {"valence": +0.8, "darkness": -0.6, "humor": +0.3})
        add("q2", "Готовы к медленному, атмосферному повествованию?", {"tempo": -0.9, "arousal": -0.3, "darkness": +0.2})
        add("q3", "Юмор — must-have сегодня?", {"humor": +0.9, "valence": +0.3})
        add("q4", "Окей ли тёмные/мрачные темы?", {"darkness": +0.9, "valence": -0.4, "violence_ok": +0.4})
        add("q5", "Хотите уложиться в ≤ 50 минут?", {"runtime_short": +0.9})
        add("q6", "Готовы к необычному/экспериментальному?", {"novelty": +0.9})
        add("q7", "Комфортно с жёсткими сценами?", {"violence_ok": +0.9, "darkness": +0.3})
        add("q8", "Скорее криминал/детектив, чем фантастика?", {"crime_pref": +0.9, "scifi_pref": -0.6})
        add("q9", "Новинка вместо классики?", {"novelty": +0.6})
        add("q10", "Окей не-англоязычное?", {"non_english_ok": +0.9})
        add("q11", "Романтическая комедия сейчас — это да?", {"romcom_pref": +0.9, "darkness": -0.7, "humor": +0.5})
        add("q12", "Документальное кино — норм?", {"doc_pref": +0.9})

        return OkkonatorConfig(
            axes=axes,
            questions=q,
            q_max=16,
            sigma_min=0.15,
            sigma_max=1.00,
            base_lr=0.60,
            entropy_target=0.35,
            coverage_lambda=0.10,
        )

# -----------------------------
# Пример использования
# -----------------------------
if __name__ == "__main__":
    engine = OkkonatorEngine()

    # Стартуем: получаем первый вопрос
    resp = engine.start()
    print("START:", resp["next_question"], "confidence:", resp["confidence_pct"], "%")

    # Ответим на 6-8 вопросов (примерно)
    steps = [
        ("q1", "Да"),
        ("q2", "Скорее нет"),
        ("q3", "Да"),
        ("q4", "Скорее да"),
        ("q5", "Скорее да"),
        ("q6", "Скорее да"),
        ("q8", "Скорее да"),
    ]

    for qid, ans in steps:
        resp = engine.step(qid, ans)
        print(f"\nANSWER: {qid=} {ans=}")
        print("confidence:", resp["confidence_pct"], "%")
        print("next_question:", resp["next_question"])
        print("complete:", resp["complete"])
        print("profile_preview:", resp["profile_preview"])

    # Можно продолжать step(...) пока complete не станет True
