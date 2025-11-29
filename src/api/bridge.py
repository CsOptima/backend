import logging
import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sqlalchemy.orm import Session

from src.core.db import db_client
from src.json.url_in import UrlIn
from src.servicies.cash_provider import CashProvider
from src.servicies.llm_asking import LLMAsker
from src.servicies.site_parser import SiteParser
from src.servicies.summarize_text import SummarizerText
from src.servicies.yandex_searcher import YandexSearcher
from src.utils.citation_analyzer import calculate_my_metrics

bridge_router = APIRouter(
    prefix="/analyze",
    tags=["Коннектор"],
)


@bridge_router.post("/")
async def analyze_site(payload: UrlIn, db_session: Session = db_client):
    try:
        url = payload.url
        if not url.startswith("http"):
            url = "https://" + url

        content = SiteParser.load_page(url)
        print(content)

        old_metrics = CashProvider.get_metric(content, db_session)

        if old_metrics:
            return {"m1": int(old_metrics[0] * 100), "m2": int(old_metrics[1] * 100), "m3": int(old_metrics[2] * 100),
                    "m4": int(old_metrics[3] * 100)}
        else:
            summary = SummarizerText.summarize_text(content)

            queries = LLMAsker.ask_llm(summary)
            print('\n'.join(queries))

            search = ""
            for query in queries:
                search += YandexSearcher.search_yandex_neuro(query)
                search += "\n"

            pos, word, citation_quality, total_score = calculate_my_metrics(search, url)
            CashProvider.put_metric(content, pos, word, citation_quality, total_score, db_session)

            return {"m1": int(pos * 100), "m2": int(word * 100), "m3": int(citation_quality * 100),
                    "m4": int(total_score * 100)}
    except Exception as exc:
        msg = '\n'.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logging.error(msg)
        raise HTTPException(500, str(exc))
