import logging
import traceback

from fastapi import APIRouter, HTTPException

from sqlalchemy.orm import Session

from src.core.db import db_client
from src.json.url_in import UrlIn
from src.servicies.html_optimizer import HTMLOptimizer


rewriter_router = APIRouter(
    prefix="/update",
    tags=["Улучшитель"],
)


@rewriter_router.post("/")
async def rewrite_site(payload: UrlIn, db_session: Session = db_client):
    try:
        url = payload.url
        if not url.startswith("http"):
            url = "https://" + url

        optimizer = HTMLOptimizer(url)

        upd_head, upd_body = await optimizer.optimize()

        return {"head": upd_head.replace('```', ''),
                "body": upd_body.replace('```', '')}
    except Exception as exc:
        msg = '\n'.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logging.error(msg)
        raise HTTPException(500, str(exc))
