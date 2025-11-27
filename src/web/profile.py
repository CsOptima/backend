from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

profile_router = APIRouter(
    prefix="/profile",
    tags=["Главная"],
)
templates = Jinja2Templates(directory="templates")


@profile_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
