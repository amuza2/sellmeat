from viewmodels.base import ViewModelBase, ObservableProperty, AsyncCommand
from models.user import UserCreate, UserLogin, UserRole
from services.api import APIClient
from auth import Session


class AuthViewModel(ViewModelBase):
    email = ObservableProperty("")
    password = ObservableProperty("")
    name = ObservableProperty("")
    phone = ObservableProperty("")
    is_seller = ObservableProperty(False)
    error = ObservableProperty("")
    is_loading = ObservableProperty(False)
    is_login_mode = ObservableProperty(True)

    def __init__(self, api: APIClient, session: Session):
        super().__init__()
        self.api = api
        self.session = session
        self.login_command = AsyncCommand(self._do_login, self._can_submit)
        self.register_command = AsyncCommand(self._do_register, self._can_submit)
        self.toggle_mode_command = lambda: self._toggle_mode()

    def _toggle_mode(self):
        self.is_login_mode = not self.is_login_mode
        self.error = ""
        self.notify("is_login_mode")

    def reset(self):
        self.email = ""
        self.password = ""
        self.name = ""
        self.phone = ""
        self.is_seller = False
        self.is_login_mode = True
        self.error = ""
        self.notify("email")
        self.notify("password")

    def _can_submit(self) -> bool:
        if not self.email or not self.password:
            return False
        if not self.is_login_mode:
            if not self.name:
                return False
            if not self.is_seller and not self.phone:
                return False
        return True

    async def _do_login(self):
        self.is_loading = True
        self.error = ""
        self.notify("is_loading")
        try:
            token = await self.api.login(UserLogin(email=self.email, password=self.password))
            self.session.set_tokens(token.access_token, token.refresh_token)
            user = await self.api.get_me()
            self.session.set_user(user)
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")

    async def _do_register(self):
        self.is_loading = True
        self.error = ""
        self.notify("is_loading")
        try:
            role = UserRole.seller if self.is_seller else UserRole.customer
            data = UserCreate(
                name=self.name,
                email=self.email,
                password=self.password,
                phone=self.phone if not self.is_seller else None,
                role=role,
            )
            await self.api.register(data)
            token = await self.api.login(UserLogin(email=self.email, password=self.password))
            self.session.set_tokens(token.access_token, token.refresh_token)
            user = await self.api.get_me()
            self.session.set_user(user)
        except Exception as e:
            self.error = str(e)
            self.notify("error")
        finally:
            self.is_loading = False
            self.notify("is_loading")
