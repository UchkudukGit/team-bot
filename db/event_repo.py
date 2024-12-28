import shutil
from pathlib import Path, PurePath

from service.models import Event

__storage: dict[(int, int), Event] = {}

DATA_DIRECTORY = 'data'
chat_ids: set[int] = set()


class EventRepo:

    def __init__(self, data_directory: str = DATA_DIRECTORY) -> None:
        self.data_directory = data_directory

    def save_event(self, event_info: Event) -> None:
        if not event_info.chat_id or not event_info.message_id:
            raise Exception('Event has not chat_id or message_id')

        path = self._create_chat_dir(event_info.chat_id)
        event_path = path.joinpath(f'{event_info.message_id}.js')
        with open(event_path, 'w', encoding='utf-8') as event_file:
            event_file.write(event_info.model_dump_json())

    def get_event(self, chat_id: int, message_id: int) -> Event:
        path = self._get_path(chat_id, message_id)
        with open(path, 'r', encoding='utf-8') as event_file:
            return Event.model_validate_json(event_file.read())

    def delete_event(self, event_info: Event) -> None:
        path = Path(self._get_path(event_info.chat_id, event_info.message_id))
        if path.exists():
            path.unlink()

    def delete_all(self) -> None:
        shutil.rmtree(Path(self._get_data_path()))

    def _get_path(self, chat_id: int, message_id: int) -> PurePath:
        return self._get_data_path().joinpath(str(chat_id)).joinpath(f'{message_id}.js')

    def _create_chat_dir(self, chat_id: int) -> PurePath:
        pure_path = self._get_data_path().joinpath(str(chat_id))
        if chat_id in chat_ids:
            return pure_path
        Path(pure_path).mkdir(parents=True, exist_ok=True)
        chat_ids.add(chat_id)
        return pure_path

    def _get_data_path(self):
        return PurePath(__file__).parent.parent.joinpath(self.data_directory)
