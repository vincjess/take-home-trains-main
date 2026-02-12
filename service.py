from typing import TypedDict

from db import Database


class SimultaneousResult(TypedDict):
    time: int | None
    trains: list[str]


class TrainService:
    # Maintains dual indexes: train:ID -> schedule and time:minutes -> [train_ids]
    # Trade-off: O(s) writes to update both indexes, but avoids O(t*s) schedule scans for overlap queries

    TRAIN_PREFIX = "train:"
    TIME_PREFIX = "time:"

    def __init__(self, db: Database) -> None:
        self._db = db

    def _train_key(self, train_id: str) -> str:
        return f"{self.TRAIN_PREFIX}{train_id}"

    def _time_key(self, time: int) -> str:
        return f"{self.TIME_PREFIX}{time}"

    def _all_times(self) -> list[int]:
        prefix_len = len(self.TIME_PREFIX)
        return [
            int(key[prefix_len:])
            for key in self._db.keys()
            if key.startswith(self.TIME_PREFIX)
        ]

    def _add_train_to_time(self, train_id: str, time: int) -> None:
        key = self._time_key(time)
        trains: list[str] = self._db.get(key) or []
        if train_id not in trains:
            trains.append(train_id)
            self._db.set(key, trains)

    def _remove_train_from_time(self, train_id: str, time: int) -> None:
        key = self._time_key(time)
        trains: list[str] = self._db.get(key) or []
        if train_id in trains:
            trains.remove(train_id)
            if trains:
                self._db.set(key, trains)
            else:
                # Clean up empty time slots
                self._db.set(key, [])

    def upsert_schedule(self, train_id: str, schedule: list[int]) -> None:
        # Get old schedule to remove from time index
        old_schedule = self.get_schedule(train_id) or []
        for time in old_schedule:
            self._remove_train_from_time(train_id, time)

        # Save new schedule
        self._db.set(self._train_key(train_id), schedule)

        # Add to time index
        for time in schedule:
            self._add_train_to_time(train_id, time)

    def get_schedule(self, train_id: str) -> list[int] | None:
        result = self._db.get(self._train_key(train_id))
        if result is None:
            return None
        return list(result)

    def find_next_simultaneous(
        self, after: int | None = None, min_trains: int = 2
    ) -> SimultaneousResult:
        """Find the next time when min_trains+ arrive simultaneously."""
        simultaneous: list[int] = []
        for time in self._all_times():
            trains: list[str] = self._db.get(self._time_key(time)) or []
            if len(trains) >= min_trains:
                simultaneous.append(time)

        simultaneous.sort()

        # If no simultaneous times, maintain the same structure as the original test case.
        if not simultaneous:
            return {"time": None, "trains": []}

        if after is None:
            target = simultaneous[0]
        else:
            target = next((t for t in simultaneous if t > after), simultaneous[0])

        trains = self._db.get(self._time_key(target)) or []
        return {"time": target, "trains": sorted(trains)}
