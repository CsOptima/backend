# Python
import math
import re
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Iterable

_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-я0-9]+", re.UNICODE)


def tokenize(text: str) -> List[str]:
    # Простейшая токенизация: буквы/цифры, нижний регистр
    return _TOKEN_RE.findall(text.lower())


def generate_ngrams(tokens: List[str], ngram_range: Tuple[int, int]) -> List[str]:
    ngrams = []
    lo, hi = ngram_range
    for n in range(lo, hi + 1):
        if n == 1:
            ngrams.extend(tokens)
        else:
            ngrams.extend([" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)])
    return ngrams


def remove_stopwords(tokens: Iterable[str], stopwords: Iterable[str] | None) -> List[str]:
    if not stopwords:
        return list(tokens)
    stop = set(stopwords)
    return [t for t in tokens if t not in stop]


def build_vocabulary(corpus_tokens: List[List[str]]) -> Dict[str, int]:
    vocab: Dict[str, int] = {}
    for doc in corpus_tokens:
        for tok in doc:
            if tok not in vocab:
                vocab[tok] = len(vocab)
    return vocab


def compute_idf(corpus_tokens: List[List[str]], vocab: Dict[str, int]) -> List[float]:
    N = len(corpus_tokens)
    df = [0] * len(vocab)
    for doc in corpus_tokens:
        seen = set()
        for tok in doc:
            idx = vocab[tok]
            if idx not in seen:
                df[idx] += 1
                seen.add(idx)
    # Сглажённый IDF: log((N + 1) / (df + 1)) + 1
    idf = [math.log((N + 1) / (df_i + 1)) + 1.0 for df_i in df]
    return idf


def l2_normalize(vec: Dict[int, float]) -> Dict[int, float]:
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {i: v / norm for i, v in vec.items()}


def to_tfidf(doc_tokens: List[str], vocab: Dict[str, int], idf: List[float]) -> Dict[int, float]:
    tf = Counter(doc_tokens)
    vec: Dict[int, float] = {}
    for tok, cnt in tf.items():
        if tok in vocab:
            idx = vocab[tok]
            vec[idx] = (cnt) * idf[idx]  # классический tf * idf (tf — частота в документе)
    return l2_normalize(vec)


def cosine_similarity_sparse(a: Dict[int, float], b: Dict[int, float]) -> float:
    # Скалярное произведение разреженных L2-нормализованных векторов
    if len(a) > len(b):
        a, b = b, a
    return sum(val * b.get(idx, 0.0) for idx, val in a.items())


def prepare_tokens(
        text: str,
        stopwords: Iterable[str] | None = None,
        ngram_range: Tuple[int, int] = (1, 1),
) -> List[str]:
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens, stopwords)
    tokens = generate_ngrams(tokens, ngram_range)
    return tokens


def tfidf_cosine_similarity(
        text_a: str,
        text_b: str,
        stopwords: Iterable[str] | None = None,
        ngram_range: Tuple[int, int] = (1, 1),
) -> float:
    # 1) Токенизация/предобработка
    doc_a = prepare_tokens(text_a, stopwords=stopwords, ngram_range=ngram_range)
    doc_b = prepare_tokens(text_b, stopwords=stopwords, ngram_range=ngram_range)

    # 2) Строим корпус только из двух документов (без обучения на внешних данных)
    corpus = [doc_a, doc_b]

    # 3) Словарь и IDF
    vocab = build_vocabulary(corpus)
    idf = compute_idf(corpus, vocab)

    # 4) Вектора TF-IDF (L2-нормированные)
    vec_a = to_tfidf(doc_a, vocab, idf)
    vec_b = to_tfidf(doc_b, vocab, idf)

    # 5) Косинусная близость
    return cosine_similarity_sparse(vec_a, vec_b)


ru_stopwords = {
    "и", "в", "во", "на", "но", "а", "что", "как", "за", "к", "с", "со", "из", "у", "от",
    "по", "для", "о", "об", "обо", "до", "при", "без", "над", "под", "про", "же", "ли",
    "либо", "ни", "да", "то", "не"
}
