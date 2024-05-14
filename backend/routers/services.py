from starlette.responses import PlainTextResponse

from backend.routers import app, Authority
from backend.routers.models import PasswordApiModel


@app.post("/services/login", response_class=PlainTextResponse)
async def service_auth(password: PasswordApiModel):
    return await Authority.service_authorization(password.password)


