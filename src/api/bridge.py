from fastapi import APIRouter, WebSocket
import asyncio
import requests

from starlette.websockets import WebSocketDisconnect
from sqlalchemy.orm import Session

from src.core.db import db_client
from src.servicies.cash_provider import CashProvider
from src.servicies.html_optimizer import HTMLOptimizer
from src.servicies.site_parser import SiteParser
from src.servicies.summarize import Summarizer
from src.servicies.text_comparator import TextComparator
from src.servicies.yandex_searcher import YandexSearcher

bridge_router = APIRouter(
    prefix="/bridge",
    tags=["Коннектор"],
)


@bridge_router.get("/")
async def get_atp_report(number: int) -> int:
    return number


@bridge_router.websocket("/counter")
async def websocket_counter(websocket: WebSocket):
    await websocket.accept()
    counter = 1
    while True:
        try:
            await websocket.send_text(str(counter))
            counter += 1
            await asyncio.sleep(1)
        except WebSocketDisconnect:
            break


@bridge_router.websocket("/load2")
async def websocket_load(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            info = await websocket.receive_text()
            await websocket.send_text("Поиск информации с помощью GEO")
            text = YandexSearcher.search_yandex_neuro(info)
            links = YandexSearcher.extract_urls(text)
            await websocket.send_text(links)
        except WebSocketDisconnect:
            break


@bridge_router.websocket("/load3")
async def websocket_load(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            info = await websocket.receive_text()

            await websocket.send_text("Получение содержимого сайта")
            text = SiteParser.extract_text(info)
            await websocket.send_text(text)

            await websocket.send_text("Получение структуры сайта")
            optimizer = HTMLOptimizer(info)

            await websocket.send_text("Отправка запроса в LLM модель")
            upd_head, upd_body = await optimizer.optimize()

            await websocket.send_text(upd_head)
            await websocket.send_text(upd_body)
        except WebSocketDisconnect:
            break


@bridge_router.websocket("/load")
async def websocket_load(websocket: WebSocket, db_session: Session = db_client):
    await websocket.accept()
    while True:
        try:
            url = await websocket.receive_text()
            if not url.startswith("http"):
                url = "https://" + url

            await websocket.send_text("Получение содержимого сайта")
            content = SiteParser.load_page(url)

            old_metric = CashProvider.get_metric(content, db_session)
            if old_metric:
                await websocket.send_text("Результат схожести текста")
                await websocket.send_text(f"Схожесть (TF-IDF, униграммы): {old_metric:.3f}")
            else:

                await websocket.send_text(content)

                await websocket.send_text("Определение предметной области")
                summary = Summarizer.summarize(content)
                await websocket.send_text(summary)

                await websocket.send_text("Поиск информации с помощью GEO")
                search = YandexSearcher.search_yandex_neuro("Воронежский транспорт")
                await websocket.send_text(search)
                links = YandexSearcher.extract_urls(search)
                await websocket.send_text(links)

                await websocket.send_text("Результат схожести текста")
                level, value = TextComparator.compare(content, search)
                CashProvider.put_metric(content, value, db_session)
                await websocket.send_text(level)


        except WebSocketDisconnect:
            break
