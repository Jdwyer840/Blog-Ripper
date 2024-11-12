import datetime
import hashlib
import json
import re
from typing import Any, Union
import zoneinfo
import rapidjson


class CoreUtilities:

    @staticmethod
    def read_file(file_path):
        with open(file_path, 'r') as file:
            file.read()

    @staticmethod
    def datetime_zoneinfo(tz: Union[str, zoneinfo.ZoneInfo]) -> zoneinfo.ZoneInfo:
        """Helper method to get zoneinfo from the specified timezone string"""
        return zoneinfo.ZoneInfo(tz) if isinstance(tz, str) else tz

    @staticmethod
    def datetime_tz_aware(value: str, tz: Any = datetime.timezone.utc) -> datetime.datetime:
        value = value.replace(' +', '+').replace(' -', '-')
        dt = datetime.datetime.fromisoformat(value)
        if not CoreUtilities.is_tz_aware(dt):
            dt = dt.replace(tzinfo=tz)
        return dt

    @staticmethod
    def is_tz_aware(dt: datetime.datetime) -> bool:
        return not (dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None)

    @staticmethod
    def configurable_hex_digest(output_size: int, data: bytes) -> str:
        """Generates a hash with a configurable output size"""
        if output_size % 2 != 0 or output_size > 128 or output_size < 2:
            raise ValueError('output_size must be even and between 2 and 128 (inclusive)')
        b = hashlib.blake2b(digest_size=int(output_size / 2))  # hexdigest() result will be 2x digest_size
        b.update(data)
        return b.hexdigest()

    @staticmethod
    def json_loads_relaxed(value: str) -> dict:
        """The standard json library will not allow comments or trailing commas,
        and third parties do not always follow the strict JSON standards"""
        try:
            return rapidjson.loads(value, parse_mode=rapidjson.PM_COMMENTS | rapidjson.PM_TRAILING_COMMAS)
        except (rapidjson.JSONDecodeError, TypeError) as e:  # convert rapidjson exception into standard json exception
            raise json.decoder.JSONDecodeError(f'{e}', '', 0)

    @staticmethod
    def slurp_json(file_path: str, mode: str = "r", relaxed: bool = False) -> dict:
        """Read entire json file into a dictionary"""
        with open(file_path, mode) as file:
            return CoreUtilities.json_loads_relaxed(file.read()) if relaxed else json.load(file)

    @staticmethod
    def regex_capture(pattern: Any, text: Any, flags: Any = 0) -> list:
        """Normalize re's unintuitive naming of re.search(), re.match(), re.findall(), etc."""
        return re.findall(pattern=pattern, string=text, flags=flags)

    @staticmethod
    def regex_matches(pattern: Any, text: Any, flags: Any = 0) -> bool:
        """Normalize re's unintuitive naming of re.search(), re.match(), re.findall(), etc."""
        return len(CoreUtilities.regex_capture(pattern=pattern, text=text, flags=flags)) > 0

    @staticmethod
    def regex_replace(pattern: Any, repl: str, text: str) -> str:
        """Normalize re's unintuitive naming of re.search(), re.match(), re.findall(), etc."""
        return re.sub(pattern=pattern, repl=repl, string=text)
