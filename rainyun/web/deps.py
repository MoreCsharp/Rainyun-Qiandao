"""FastAPI 依赖注入。"""

from fastapi import Depends, Header

from rainyun.data.store import DataStore
from rainyun.web.auth import verify_token
from rainyun.web.errors import AuthError


_store = DataStore()


def get_store() -> DataStore:
    if _store.data is None:
        _store.load()
    return _store


def require_auth(
    authorization: str | None = Header(default=None),
    store: DataStore = Depends(get_store),
) -> dict | None:
    data = store.load() if store.data is None else store.data
    auth_config = data.settings.auth
    if not auth_config.enabled:
        return None
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("未登录")
    token = authorization.split(" ", 1)[1]
    if not auth_config.token.secret:
        raise AuthError("未配置 Token 密钥")
    payload = verify_token(token, auth_config.token.secret)
    if payload is None:
        raise AuthError("Token 无效或已过期")
    return payload
