from typing import TypedDict

from db import Database


class SimultaneousResult(TypedDict):
    time: int | None
    trains: list[str]


class TrainService:
    TRAIN_PREFIX = "train:"

    def __init__(self, db: Database) -> None:
        self._db = db

    def _train_key(self, train_id: str) -> str:
        return f"{self.TRAIN_PREFIX}{train_id}"

    def _all_train_ids(self) -> list[str]:
        prefix_len = len(self.TRAIN_PREFIX)
        return [
            key[prefix_len:]
            for key in self._db.keys()
            if key.startswith(self.TRAIN_PREFIX)
        ]

    def upsert_schedule(self, train_id: str, schedule: list[int]) -> None:
        self._db.set(self._train_key(train_id), schedule)

    def get_schedule(self, train_id: str) -> list[int] | None:
        result = self._db.get(self._train_key(train_id))
        if result is None:
            return None
        return list(result)

    def find_next_simultaneous(
        self, after: int | None = None, min_trains: int = 2
    ) -> SimultaneousResult:
        """Find the next time when min_trains+ arrive simultaneously."""
        # Build time -> trains map by scanning all schedule.
        time_to_trains: dict[int, list[str]] = {}
        for train_id in self._all_train_ids():
            schedule = self._db.get(self._train_key(train_id)) or []
            for time in schedule:
                if time not in time_to_trains:
                    time_to_trains[time] = []
                time_to_trains[time].append(train_id)

        # Find times with enough trains
        simultaneous = [
            time for time, trains in time_to_trains.items() if len(trains) >= min_trains
        ]
        simultaneous.sort()

        if not simultaneous:
            return {"time": None, "trains": []}

        if after is None:
            target = simultaneous[0]
        else:
            target = next((t for t in simultaneous if t > after), simultaneous[0])

        return {"time": target, "trains": sorted(time_to_trains[target])}
