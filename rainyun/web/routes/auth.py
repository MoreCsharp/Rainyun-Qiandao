"""鉴权路由。"""

import secrets

from fastapi import APIRouter, Body, Depends

from rainyun.data.store import DataStore
from rainyun.web.auth import hash_password, issue_token, verify_password
from rainyun.web.deps import get_store
from rainyun.web.errors import ApiError, AuthError
from rainyun.web.responses import success_response

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login")
def login(payload: dict = Body(default_factory=dict), store: DataStore = Depends(get_store)) -> dict:
    data = store.load() if store.data is None else store.data
    password = payload.get("password", "")
    if not isinstance(password, str) or not password:
        raise ApiError("密码不能为空", status_code=400)

    auth_config = data.settings.auth
    if not auth_config.password_hash:
        auth_config.password_hash = hash_password(password)

    if not verify_password(password, auth_config.password_hash):
        raise AuthError("密码错误")

    if not auth_config.token.secret:
        auth_config.token.secret = secrets.token_urlsafe(32)

    store.update_settings(data.settings)
    token = issue_token("admin", auth_config.token.secret, auth_config.token.expires_in_days)
    return success_response({"token": token, "expires_in_days": auth_config.token.expires_in_days})
