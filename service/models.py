import logging
from enum import Enum

from telegram import User

logger = logging.getLogger('service')

SEPARATOR = '-' * 10

def user_to_str(user: User) -> str:
    username = user.username
    if user.full_name:
        return f'@{username} ({user.full_name})'
    return username

class ButtonAction(Enum):
    ADD_ACTIVE_USER = 'ADD_ACTIVE_USER'
    ADD_INACTIVE_USER = 'ADD_INACTIVE_USER'
    OPEN_EVENT = 'OPEN_EVENT'
    CLOSE_EVENT = 'CLOSE_EVENT'

class EventStatus(Enum):
    OPENED = 'OPENED'
    CLOSED = 'CLOSED'
    DELETED = 'DELETED'

class AddedUsers:
    def __init__(self, from_user: User):
        count_added_users = 1
        self.from_user = from_user



class EventInfo:
    def __init__(self, event_name: str):
        self.event_name: str = event_name
        self.status: EventStatus = EventStatus.OPENED
        self._chat_id: int | None = None
        self._message_id: int | None = None
        self.total_active: int = 0
        self.active_users: list[User] = []
        self.inactive_users: list[User] = []
        self.added_users: list[(int, User)] = []

    def create_key(self, chat_id: int, message_id: int)-> None:
        if self._chat_id or self._message_id:
            raise Exception('Already created key')
        self._chat_id = chat_id
        self._message_id = message_id

    def get_key(self) -> tuple[int, int] | None:
        if self._chat_id and self._message_id:
            return self._chat_id, self._message_id
        return None

    def add_active_user(self, user: User) -> None:
        if user not in self.active_users:
            self.active_users.append(user)
            self.total_active += 1

        if user in self.inactive_users:
            self.inactive_users.remove(user)

    def add_inactive_user(self, user: User) -> None:
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

        result_str_array.append(SEPARATOR)
        result_str_array.append(self._total_str())
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
