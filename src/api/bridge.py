from fastapi import APIRouter, WebSocket
import asyncio
import requests

from starlette.websockets import WebSocketDisconnect

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


@bridge_router.websocket("/load")
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
