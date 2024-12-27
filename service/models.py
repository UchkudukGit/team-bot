import logging
from enum import Enum

from pydantic import BaseModel, Field
from telegram import User

logger = logging.getLogger('service')

class ButtonAction(Enum):
    ADD_ACTIVE_USER = 'ADD_ACTIVE_USER'
    ADD_INACTIVE_USER = 'ADD_INACTIVE_USER'
    OPEN_EVENT = 'OPEN_EVENT'
    CLOSE_EVENT = 'CLOSE_EVENT'

class EventStatus(Enum):
    OPENED = 'OPENED'
    CLOSED = 'CLOSED'
    DELETED = 'DELETED'

class ShortUser(BaseModel):
    full_name: str
    username: str

    @classmethod
    def from_user(cls, user: User) -> 'ShortUser':
        return ShortUser(
            full_name=user.full_name,
            username=user.name
        )

# class AddedUsers:
#     def __init__(self, from_user: User):
#         count_added_users = 1
#         self.from_user = from_user

class Event(BaseModel):
    event_name: str
    status: EventStatus = EventStatus.OPENED
    chat_id: int | None = None
    message_id: int | None = None
    total_active: int = 0
    active_users: list[ShortUser] = []
    inactive_users: list[ShortUser] = []

    def create_key(self, chat_id: int, message_id: int)-> None:
        if self.chat_id or self.message_id:
            raise Exception('Already created key')
        self.chat_id = chat_id
        self.message_id = message_id

    def get_key(self) -> tuple[int, int] | None:
        if self.chat_id and self.message_id:
            return self.chat_id, self.message_id
        return None

    def add_active_user(self, telegram_user: User) -> None:
        user = ShortUser.from_user(telegram_user)
        if user not in self.active_users:
            self.active_users.append(user)
            self.total_active += 1

        if user in self.inactive_users:
            self.inactive_users.remove(user)

    def add_inactive_user(self, telegram_user: User) -> None:
        user = ShortUser.from_user(telegram_user)
        if user not in self.inactive_users:
            self.inactive_users.append(user)

        if user in self.active_users:
            self.active_users.remove(user)
            self.total_active -= 1

    def to_str(self):
        return self.__str__()

    def __str__(self) -> str:
        result_str_array = [f'{self.event_name}\n']
        if self.active_users:
            result_str_array.append(self._active_users_to_str())
        if self.inactive_users:
            result_str_array.append(self._inactive_users_to_str())

        result_str_array.append(f'\n{self._total_str()}')
        return '\n'.join(result_str_array)

    def _active_users_to_str(self) -> str:
        return '\n'.join([f'✅ {user_to_str(user)}' for user in self.active_users])

    def _inactive_users_to_str(self) -> str:
        return '\n'.join([f'❌ {user_to_str(user)}' for user in self.inactive_users])

    def _total_str(self) -> str:
        result_str_array = [f'всего идут: {self.total_active}']
        if self.active_users:
            result_str_array.append(f'✅  {len(self.active_users)}')
        if self.inactive_users:
            result_str_array.append(f'❌  {len(self.inactive_users)}')
        return '\n'.join(result_str_array)


def user_to_str(user: ShortUser) -> str:
    username = user.username
    if user.full_name:
        return f'{username} {user.full_name}'
    return username