import logging
from enum import Enum

from pydantic import BaseModel, Field
from telegram import User

logger = logging.getLogger('service')

class ButtonAction(Enum):
    ADD_ACTIVE_USER = 'ADD_ACTIVE_USER'
    ADD_INACTIVE_USER = 'ADD_INACTIVE_USER'
    ADD_FROM_ME = 'ADD_FROM_ME'
    REMOVE_FROM_ME = 'REMOVE_FROM_ME'
    OPEN_EVENT = 'OPEN_EVENT'
    CLOSE_EVENT = 'CLOSE_EVENT'
    DELETE_EVENT = 'DELETE_EVENT'
    DELETE_COMPLETELY = 'DELETE_COMPLETELY'

class EventStatus(Enum):
    OPENED = 'OPENED'
    CLOSED = 'CLOSED'
    DELETED = 'DELETED'

class ShortUser(BaseModel):
    full_name: str
    username: str
    is_me: bool = True

    def __str__(self) -> str:
        name = self.full_name
        if self.username.startswith('@'):
            name = f'{self.username} {name}'
        if self.is_me:
            return f'✅ {name}'
        return f'1️⃣ от {name}'

    @classmethod
    def from_user(cls, user: User, is_me=True) -> 'ShortUser':
        return ShortUser(
            full_name=user.full_name,
            username=user.name,
            is_me=is_me,
        )

class Event(BaseModel):
    owner: ShortUser
    name: str
    limit: int | None = None
    reserve: int | None = None
    status: EventStatus = EventStatus.OPENED
    chat_id: int | None = None
    message_id: int | None = None
    active_users: list[ShortUser] = []
    inactive_users: list[ShortUser] = []

    def create_key(self, chat_id: int, message_id: int)-> None:
        if self.chat_id or self.message_id:
            raise Exception('Already created key')
        self.chat_id = chat_id
        self.message_id = message_id

    def is_owner(self, telegram_user: User) -> bool:
        return ShortUser.from_user(telegram_user) == self.owner

    def add_active_user(self, telegram_user: User) -> bool:
        user = ShortUser.from_user(telegram_user)
        if user in self.active_users:
            return False

        self.active_users.append(user)

        if user in self.inactive_users:
            self.inactive_users.remove(user)

        return True

    def add_user_from_me(self, telegram_user: User) -> None:
        user = ShortUser.from_user(telegram_user, is_me=False)
        self.active_users.append(user)

    def remove_user_from_me(self, telegram_user: User) -> bool:
        user = ShortUser.from_user(telegram_user, is_me=False)
        for i in range(len(self.active_users) - 1, -1, -1):
            if self.active_users[i] == user:
                self.active_users.pop(i)
                return True
        return False

    def add_inactive_user(self, telegram_user: User) -> bool:
        user = ShortUser.from_user(telegram_user)
        if user in self.inactive_users:
            return False

        self.inactive_users.append(user)

        if user in self.active_users:
            self.active_users.remove(user)
        return True

    def to_str(self):
        return self.__str__()

    def __str__(self) -> str:
        separator = '-' * 20
        result_str_array = [f'{self.name}\nсоздал {self.owner.username}']
        if self.limit:
            result_str_array.append(f'limit: {self.limit}')
            if self.reserve:
                result_str_array.append(f'reserve: {self.reserve}')
        result_str_array.append('\n')
        if self.active_users:
            result_str_array.append(self._active_users_to_str())
        if self.inactive_users:
            result_str_array.append(separator)
            result_str_array.append(self._inactive_users_to_str())

        result_str_array.append(f'\n{self._total_str()}')
        return '\n'.join(result_str_array)

    def _active_users_to_str(self) -> str:
        users_str_array = []
        for index, user in enumerate(self.active_users):
            if self.limit:
                if index == self.limit:
                    users_str_array.append('\nЗапасные:')
                if self.reserve and index == self.limit + self.reserve:
                    users_str_array.append('\nРезерв:')
            users_str_array.append(f'{index + 1} {user}')
        return '\n'.join(users_str_array)

    def _inactive_users_to_str(self) -> str:
        return '\n'.join([f'❌ {user_to_str(user)}' for user in self.inactive_users])

    def _total_str(self) -> str:
        result_str_array = [f'всего идут: {len(self.active_users)}']
        if self.active_users:
            main_users_count = len([user for user in self.active_users if user.is_me])
            added_users_count = len([user for user in self.active_users if not user.is_me])
            if main_users_count:
                result_str_array.append(f'✅  {main_users_count}')
            if added_users_count:
                result_str_array.append(f'➕  {added_users_count}')
        if self.inactive_users:
            result_str_array.append(f'❌  {len(self.inactive_users)}')
        return '\n'.join(result_str_array)


def user_to_str(user: ShortUser) -> str:

    full_name = user.full_name
    if user.username.startswith('@'):
        return f'{user.username} {full_name}'
    return full_name