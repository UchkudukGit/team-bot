import re

import pytest

from db.event_repo import EventRepo
from models import Event

CHAT_ID = 200
MESSAGE_ID = 100


@pytest.fixture
def db_clean(event_repo):
    # Действия перед тестом (если нужно)
    print("\nTest is starting...\n")

    yield  # Здесь происходит выполнение теста

    # Действия после теста
    event_repo.delete_all()
    print("\nTest is finished. Cleanup db.\n")


@pytest.fixture
def event_repo() -> EventRepo:
    return EventRepo(data_directory='test/data')


@pytest.fixture
def event() -> Event:
    return Event(
        name='event',
        chat_id=CHAT_ID,
        message_id=MESSAGE_ID,
    )


def test_save_event_info_success(db_clean, event_repo, event):
    event_repo.save_event(event)
    event_test = event_repo.get_event(CHAT_ID, MESSAGE_ID)
    assert event_test == event


def test():
    input_string = 'name="значение с пробелами" limit=12 reserve=2'
    d = parse_key_value_string(input_string)
    print(d)

def parse_key_value_string(s) -> dict[str, str]:
    # Регулярное выражение для поиска пар ключ=значение
    pattern = r'(\w+)=(".*?"|\S+)'
    matches = re.findall(pattern, s)

    # Преобразуем список кортежей в словарь
    result = {key: value.strip('"') for key, value in matches}
    return result
