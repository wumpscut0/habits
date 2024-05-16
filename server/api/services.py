from starlette.responses import PlainTextResponse

from server.api import app, Authority
from server.api.models import PasswordApiModel


@app.post("/services/login", response_class=PlainTextResponse)
async def service_auth(password: PasswordApiModel):
    return await Authority.service_authorization(password.password)
