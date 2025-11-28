"""
Модуль для анализа качества цитирования сайтов в ответах нейросети.

Вычисляет три метрики:
- Pos: позиционный вес (экспоненциальное затухание)
- Word: доля текста, цитирующего сайт
- CitationQuality: качество цитирования
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


@dataclass
class Citation:
    """Представляет одну цитату (ссылку) в тексте."""
    domain: str
    position: int  # Позиция в общем списке ссылок (0-based)
    paragraph_index: int  # Индекс абзаца
    index_in_group: int  # Позиция внутри группы ссылок
    group_size: int  # Размер группы ссылок
    window_words: int  # Количество слов в окне цитирования


@dataclass
class ParagraphData:
    """Данные об абзаце с его ссылками."""
    text: str
    word_count: int
    citations: List[str] = field(default_factory=list)


@dataclass
class SiteMetrics:
    """Метрики для одного сайта."""
    pos: float = 0.0
    word: float = 0.0
    citation_quality: float = 0.0
    total_score: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "pos": round(self.pos, 4),
            "word": round(self.word, 4),
            "citation_quality": round(self.citation_quality, 4),
            "total_score": round(self.total_score, 4)
        }


class CitationAnalyzer:
    """
    Анализатор качества цитирования сайтов в ответах нейросети.

    Attributes:
        target_site: Целевой сайт для анализа
    """

    # Регулярное выражение для извлечения доменов
    # Поддерживает: example.com, www.example.com, https://example.com/path
    # А также домены с TLD второго уровня: example.co.uk, example.ru
    DOMAIN_PATTERN = re.compile(
        r'(?:https?://)?'  # Опциональный протокол
        r'(?:www\.)?'  # Опциональный www
        r'('  # Начало группы захвата домена
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'  # Домен второго уровня
        r'\.'  # Точка
        r'(?:[a-zA-Z]{2,})'  # TLD или первая часть составного TLD
        r'(?:\.[a-zA-Z]{2,})?'  # Опциональная вторая часть TLD (co.uk, com.ru)
        r')'  # Конец группы захвата
        r'(?:/[^\s,;.]*)?',  # Опциональный путь
        re.IGNORECASE
    )

    # Паттерн для разделения склеенных доменов
    GLUED_DOMAIN_PATTERN = re.compile(
        r'([a-zA-Z0-9-]+\.(?:com|ru|org|net|co\.uk|io|info|biz|edu|gov|uk|de|fr|es|it|nl|eu|us|ca|au|jp|cn|in|br|mx|pl|cz|sk|ua|by|kz|[a-z]{2,3}(?:\.[a-z]{2})?))'
        r'(?=[a-zA-Z0-9])',
        re.IGNORECASE
    )

    # Разделители между ссылками
    LINK_SEPARATORS = re.compile(r'[\s,;]+')

    def __init__(self, target_site: str):
        """
        Инициализация анализатора.

        Args:
            target_site: Домен целевого сайта (например, 'botanichka.ru')
        """
        self.target_site = self._normalize_domain(target_site)
        self._all_citations: List[Citation] = []
        self._site_citations: Dict[str, List[Citation]] = defaultdict(list)
        self._total_words: int = 0
        self._paragraphs: List[ParagraphData] = []

    def _normalize_domain(self, domain: str) -> str:
        """
        Нормализует домен, удаляя протокол, www и путь.

        Args:
            domain: Исходный домен или URL

        Returns:
            Нормализованный домен в нижнем регистре
        """
        domain = domain.lower().strip()
        # Удаляем протокол
        domain = re.sub(r'^https?://', '', domain)
        # Удаляем www
        domain = re.sub(r'^www\.', '', domain)
        # Удаляем путь
        domain = domain.split('/')[0]
        # Удаляем порт
        domain = domain.split(':')[0]
        return domain

    def _extract_domains_from_text(self, text: str) -> List[str]:
        """
        Извлекает все домены из текста, включая склеенные.

        Args:
            text: Текст для анализа

        Returns:
            Список найденных доменов
        """
        domains = []

        # Сначала пытаемся разделить склеенные домены
        processed_text = text

        # Находим и разделяем склеенные домены
        glued_matches = list(self.GLUED_DOMAIN_PATTERN.finditer(processed_text))
        if glued_matches:
            # Вставляем пробелы между склеенными доменами
            offset = 0
            for match in glued_matches:
                insert_pos = match.end() + offset
                processed_text = processed_text[:insert_pos] + ' ' + processed_text[insert_pos:]
                offset += 1

        # Теперь извлекаем все домены
        for match in self.DOMAIN_PATTERN.finditer(processed_text):
            domain = self._normalize_domain(match.group(1))
            if domain and len(domain) > 3:  # Минимальная длина домена (a.ru)
                domains.append(domain)

        return domains

    def _split_into_paragraphs(self, text: str) -> List[Tuple[str, List[str]]]:
        """
        Разбивает текст на абзацы и извлекает ссылки после каждого.

        Args:
            text: Полный текст ответа

        Returns:
            Список кортежей (текст_абзаца, список_ссылок)
        """
        # Разбиваем на абзацы по пустым строкам или двойным переносам
        paragraphs_raw = re.split(r'\n\s*\n|\n{2,}', text.strip())

        result = []

        for para in paragraphs_raw:
            if not para.strip():
                continue

            # Разбиваем абзац на строки
            lines = para.strip().split('\n')

            text_lines = []
            citation_lines = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Проверяем, является ли строка преимущественно ссылками
                domains_in_line = self._extract_domains_from_text(line)
                words_in_line = len(re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]+\b', line))

                # Если в строке больше доменов или это короткая строка с доменами
                if domains_in_line and (len(domains_in_line) >= words_in_line / 3 or words_in_line < 5):
                    citation_lines.extend(domains_in_line)
                else:
                    text_lines.append(line)

            if text_lines:
                paragraph_text = ' '.join(text_lines)
                result.append((paragraph_text, citation_lines))

        # Обрабатываем случай, когда ссылки в конце текста без абзаца
        # или привязываем ссылки к предыдущему абзацу
        processed_result = []
        i = 0
        while i < len(result):
            para_text, citations = result[i]

            # Если текущий абзац пустой, но есть ссылки - привязываем к предыдущему
            if not para_text.strip() and citations and processed_result:
                prev_text, prev_citations = processed_result[-1]
                processed_result[-1] = (prev_text, prev_citations + citations)
            else:
                processed_result.append((para_text, citations))

            i += 1

        return processed_result

    def _parse_response(self, response_text: str) -> None:
        """
        Парсит ответ нейросети и извлекает все цитаты.

        Args:
            response_text: Текст ответа нейросети
        """
        self._all_citations = []
        self._site_citations = defaultdict(list)
        self._paragraphs = []

        paragraphs = self._split_into_paragraphs(response_text)

        global_position = 0
        total_words = 0

        for para_idx, (para_text, citations) in enumerate(paragraphs):
            word_count = len(re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]+\b', para_text))
            total_words += word_count

            para_data = ParagraphData(
                text=para_text,
                word_count=word_count,
                citations=citations
            )
            self._paragraphs.append(para_data)

            # Создаём объекты Citation для каждой ссылки
            group_size = len(citations)
            for idx_in_group, domain in enumerate(citations):
                citation = Citation(
                    domain=domain,
                    position=global_position,
                    paragraph_index=para_idx,
                    index_in_group=idx_in_group,
                    group_size=group_size,
                    window_words=word_count
                )
                self._all_citations.append(citation)
                self._site_citations[domain].append(citation)
                global_position += 1

        self._total_words = total_words

    def _calculate_pos(self, site: str) -> float:
        """
        Вычисляет позиционный вес для сайта.

        Формула: raw_pos = Σ(10 * 0.5^(position))
        Нормализация: pos = raw_pos / 10

        Args:
            site: Домен сайта

        Returns:
            Нормализованное значение Pos в диапазоне [0, 1]
        """
        citations = self._site_citations.get(site, [])
        if not citations:
            return 0.0

        raw_pos = sum(10 * (0.5 ** c.position) for c in citations)

        # Нормализуем делением на 10 (максимальное значение при position=0)
        pos = raw_pos / 10

        return min(pos, 1.0)

    def _calculate_word(self, site: str) -> float:
        """
        Вычисляет долю текста, цитирующего сайт.

        Args:
            site: Домен сайта

        Returns:
            Значение Word в диапазоне [0, 1]
        """
        if self._total_words == 0:
            return 0.0

        citations = self._site_citations.get(site, [])
        if not citations:
            return 0.0

        # Группируем цитаты по абзацам
        para_citations: Dict[int, List[Citation]] = defaultdict(list)
        for c in citations:
            para_citations[c.paragraph_index].append(c)

        total_attributed = 0.0

        for para_idx, site_citations in para_citations.items():
            if para_idx >= len(self._paragraphs):
                continue

            para = self._paragraphs[para_idx]
            window_words = para.word_count

            # Определяем общее количество уникальных сайтов в этом абзаце
            total_citations_in_para = len(para.citations)

            if total_citations_in_para == 0:
                continue

            # Количество упоминаний нашего сайта в этом абзаце
            site_mentions = len(site_citations)

            # Атрибутируем слова пропорционально
            attributed = (window_words * site_mentions) / total_citations_in_para
            total_attributed += attributed

        word = total_attributed / self._total_words
        return min(word, 1.0)

    def _calculate_citation_quality(self, site: str) -> float:
        """
        Вычисляет качество цитирования для сайта.

        Учитывает:
        - Длину блока (>20 слов = бонус)
        - Позицию в группе ссылок
        - Соло vs групповое цитирование
        - Уникальность (единственная ссылка)

        Args:
            site: Домен сайта

        Returns:
            Значение CitationQuality в диапазоне [0, 1]
        """
        citations = self._site_citations.get(site, [])
        if not citations:
            return 0.0

        # Определяем типы цитирования
        has_solo = any(c.group_size == 1 for c in citations)
        has_group = any(c.group_size > 1 for c in citations)

        # Solo/Group factor
        if has_solo and has_group:
            solo_group_factor = 1.0
        elif has_solo:
            solo_group_factor = 0.9
        else:
            solo_group_factor = 0.7

        # Проверяем уникальность
        total_unique_sites = len(self._site_citations)
        is_unique = total_unique_sites == 1 and len(self._all_citations) == 1
        unique_bonus = 0.1 if is_unique else 0.0

        # Вычисляем качество для каждой цитаты и усредняем
        quality_scores = []

        for c in citations:
            # Base: обратно пропорционально размеру группы
            base = 1.0 / c.group_size

            # Бонус за позицию в группе (0-я позиция лучшая)
            pos_bonus = max(0, 0.3 - 0.1 * c.index_in_group)

            # Бонус за длину блока
            length_bonus = 0.2 if c.window_words > 20 else 0.0

            raw_quality = base + pos_bonus + length_bonus
            quality_scores.append(raw_quality)

        # Усредняем качество по всем цитатам
        avg_quality = sum(quality_scores) / len(quality_scores)

        # Применяем факторы
        citation_quality = min(avg_quality * solo_group_factor + unique_bonus, 1.0)

        return citation_quality

    def _calculate_metrics_for_site(self, site: str) -> SiteMetrics:
        """
        Вычисляет все метрики для указанного сайта.

        Args:
            site: Домен сайта

        Returns:
            Объект SiteMetrics с вычисленными метриками
        """
        metrics = SiteMetrics()
        metrics.pos = self._calculate_pos(site)
        metrics.word = self._calculate_word(site)
        metrics.citation_quality = self._calculate_citation_quality(site)
        metrics.total_score = (
                metrics.pos * 0.6 +
                metrics.word * 0.3 +
                metrics.citation_quality * 0.1
        )
        return metrics

    def evaluate(self, response_text: str) -> Dict[str, any]:
        """
        Оценивает качество цитирования в ответе нейросети.

        Args:
            response_text: Текст ответа нейросети

        Returns:
            Словарь с метриками для целевого сайта, конкурентов и лучшего конкурента
        """
        # Парсим ответ
        self._parse_response(response_text)

        # Вычисляем метрики для целевого сайта
        target_metrics = self._calculate_metrics_for_site(self.target_site)

        # Вычисляем метрики для конкурентов
        competitors_metrics: Dict[str, Dict[str, float]] = {}
        for site in self._site_citations.keys():
            if site != self.target_site:
                site_metrics = self._calculate_metrics_for_site(site)
                competitors_metrics[site] = site_metrics.to_dict()

        # Находим лучшего конкурента
        best_competitor = {"site": None, "score": 0.0}
        for site, metrics in competitors_metrics.items():
            if metrics["total_score"] > best_competitor["score"]:
                best_competitor = {"site": site, "score": round(metrics["total_score"], 4)}

        return {
            "pos": round(target_metrics.pos, 4),
            "word": round(target_metrics.word, 4),
            "citation_quality": round(target_metrics.citation_quality, 4),
            "total_score": round(target_metrics.total_score, 4),
            "competitors": competitors_metrics,
            "best_competitor": best_competitor
        }

    def get_all_sites(self) -> Set[str]:
        """
        Возвращает все найденные сайты в ответе.

        Returns:
            Множество доменов
        """
        return set(self._site_citations.keys())

    def get_citation_details(self) -> List[Dict]:
        """
        Возвращает детальную информацию о всех цитатах.

        Returns:
            Список словарей с информацией о каждой цитате
        """
        return [
            {
                "domain": c.domain,
                "position": c.position,
                "paragraph_index": c.paragraph_index,
                "index_in_group": c.index_in_group,
                "group_size": c.group_size,
                "window_words": c.window_words
            }
            for c in self._all_citations
        ]


def calculate_metrics(response_text: str, target_site: str) -> Dict[str, any]:
    """
    Удобная функция для быстрого вычисления метрик.

    Args:
        response_text: Текст ответа нейросети
        target_site: Целевой сайт для анализа

    Returns:
        Словарь с метриками
    """
    analyzer = CitationAnalyzer(target_site)
    return analyzer.evaluate(response_text)


# Пример использования
def calculate_my_metrics(response, url):
    # Вычисляем метрики
    result = calculate_metrics(response, url)

    answer = []
    answer.append(f"  Pos (позиционный вес):     {result['pos']:.4f}")
    answer.append(f"  Word (доля текста):        {result['word']:.4f}")
    answer.append(f"  Citation Quality:          {result['citation_quality']:.4f}")
    answer.append(f"  Total Score:               {result['total_score']:.4f}")

    answer.append(f"\nКонкуренты:")
    for site, metrics in result['competitors'].items():
        answer.append(f"  {site}:")
        answer.append(f"    Total Score: {metrics['total_score']:.4f}")
    #answer.append(f"\nЛучший конкурент:")
    #answer.append(f"  {result['best_competitor']['site']}: {result['best_competitor']['score']:.4f}")
    return result['pos'], result['word'], result['citation_quality'], result['total_score']
    #return '\n'.join(answer)