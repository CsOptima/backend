import logging
import traceback

from fastapi import APIRouter, HTTPException

from sqlalchemy.orm import Session

from src.core.db import db_client
from src.servicies.html_optimizer import HTMLOptimizer


rewriter_router = APIRouter(
    prefix="/rewriter",
    tags=["Улучшитель"],
)


@rewriter_router.get("/")
async def rewrite_site(url: str, db_session: Session = db_client):
    try:
        if not url.startswith("http"):
            url = "https://" + url

        optimizer = HTMLOptimizer(url)

        upd_head, upd_body = await optimizer.optimize()

        return {"upd_head": upd_head,
                "upd_body": upd_body}
    except Exception as exc:
        msg = '\n'.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logging.error(msg)
        raise HTTPException(500, str(exc))
