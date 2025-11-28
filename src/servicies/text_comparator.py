from src.utils.cosinus_comparator import tfidf_cosine_similarity, ru_stopwords


class TextComparator:
    @staticmethod
    def compare(text1, text2):
        sim_unigram = tfidf_cosine_similarity(text1, text2, stopwords=ru_stopwords, ngram_range=(1, 1))
        sim_bigrams = tfidf_cosine_similarity(text1, text2, stopwords=ru_stopwords, ngram_range=(1, 2))

        return f"Схожесть (TF-IDF, униграммы): {sim_unigram:.3f} Схожесть (TF-IDF, 1-2 граммы): {sim_bigrams:.3f}"
