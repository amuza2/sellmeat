import json
import os
from models.user import User


SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".session.json")


class Session:
    """Manages authentication tokens and current user session."""

    def __init__(self):
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._user: User | None = None
        self._load()

    def _load(self):
        try:
            if os.path.exists(SESSION_FILE):
                with open(SESSION_FILE, "r") as f:
                    data = json.load(f)
                    self._access_token = data.get("access_token")
                    self._refresh_token = data.get("refresh_token")
                    if data.get("user"):
                        self._user = User(**data["user"])
        except Exception:
            pass

    def _save(self):
        try:
            data = {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
                "user": self._user.model_dump(mode="json") if self._user else None,
            }
            with open(SESSION_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _clear(self):
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
        except Exception:
            pass

    @property
    def access_token(self) -> str | None:
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    @property
    def user(self) -> User | None:
        return self._user

    @property
    def is_authenticated(self) -> bool:
        return self._access_token is not None

    @property
    def is_seller(self) -> bool:
        return self._user is not None and self._user.role.value == "seller"

    def set_tokens(self, access: str, refresh: str):
        self._access_token = access
        self._refresh_token = refresh
        self._save()

    def set_user(self, user: User):
        self._user = user
        self._save()

    def logout(self):
        self._access_token = None
        self._refresh_token = None
        self._user = None
        self._clear()
