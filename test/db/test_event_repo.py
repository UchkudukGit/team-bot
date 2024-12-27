import pytest

from db.event_repo import EventRepo
from service.models import Event

CHAT_ID = 200
MESSAGE_ID = 100



@pytest.fixture
def db_clean(event_repo):
    # Действия перед тестом (если нужно)
    print("\nTest is starting...")

    yield  # Здесь происходит выполнение теста

    # Действия после теста
    event_repo.delete_all()
    print("\nTest is finished. Cleanup db.")

@pytest.fixture
def event_repo() -> EventRepo:
    return EventRepo('test1/data')

@pytest.fixture
def event() -> Event:
    return Event(
        event_name='event',
        chat_id=CHAT_ID,
        message_id=MESSAGE_ID,
    )

def test_save_event_info_success(db_clean, event_repo, event):
    event_repo.save_event(event)
    event_test = event_repo.get_event(CHAT_ID, MESSAGE_ID)
    assert event_test == event
