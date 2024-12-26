import logging

from service.models import EventInfo

__storage: dict[(int, int), EventInfo] = {}

def save_event_info(event_info: EventInfo) -> None:
    key = event_info.get_key()
    if not key:
        raise Exception('Event has not key')
    __storage[key] = event_info

def get_event_info(key: (int, int)) -> EventInfo:
    if key not in __storage:
        raise Exception('Event not found')
    return __storage[key]
