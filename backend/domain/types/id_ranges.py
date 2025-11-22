from typing import Any


class IdRanges:
    def __init__(self, ranges: list[dict[str, Any]]):
        self.ranges = ranges

    def contains(self, location_id: int) -> bool:
        for range_def in self.ranges:
            min_id = range_def.get("min")
            max_id = range_def.get("max")

            if min_id is not None and max_id is not None and min_id <= location_id <= max_id:
                return True

        return False

    def get_type(self, location_id: int) -> str | None:
        for range_def in self.ranges:
            min_id = range_def.get("min")
            max_id = range_def.get("max")
            location_type = range_def.get("type")

            if (
                min_id is not None
                and max_id is not None
                and location_type
                and min_id <= location_id <= max_id
            ):
                return location_type

        return None
