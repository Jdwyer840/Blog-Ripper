import datetime
import hashlib
import json
import re
from typing import Any, Union
import zoneinfo
import rapidjson


class CoreUtilities:

    datetime_formats_ymd_standard = '%Y-%m-%d'
    datetime_formats_ymd_underscores = '%Y_%m_%d'
    datetime_formats_ymd_forward_slash = '%Y/%m/%d'

    datetime_formats_ymdhms_standard = datetime_formats_ymd_standard + ' ' + '%H:%M:%S'
    datetime_formats_ymdhmsz_standard = datetime_formats_ymdhms_standard + " %Z"
    datetime_formats_ymd_tight = '%Y%m%d'
    datetime_formats_ymdhms_tight = datetime_formats_ymd_tight + '%H%M%S'

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

    @staticmethod
    def extract_date_format_from_date_str(date_str: str, return_datetime: bool = False) -> str | datetime.datetime | None:
        formats_to_try = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y/%m/%d",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S.%f",

            "%m-%d-%Y",
            "%m-%d-%y",
            "%m-%d-%Y %H:%M",
            "%m-%d-%Y %H:%M:%S",
            "%m-%d-%Y %H:%M:%S.%f",
            "%m/%d/%Y",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S.%f",

            "%d-%m-%Y",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S.%f",
            "%d/%m/%Y",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S.%f",

            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y/%m/%dT%H:%M",
            "%Y/%m/%dT%H:%M:%S",
            "%Y/%m/%dT%H:%M:%S.%f",
            "%Y.%m.%d",
            "%Y.%m.%d %H:%M",
            "%Y.%m.%d %H:%M:%S",
            "%Y.%m.%d %H:%M:%S.%f",

            "%d.%m.%Y",
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y %H:%M:%S",
            "%d.%m.%Y %H:%M:%S.%f",

            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",

            "%B %d, %Y"
        ]

        for date_format in formats_to_try:
            try:
                parsed = datetime.datetime.strptime(date_str, date_format)
                if return_datetime:
                    return parsed
                return date_format
            except ValueError:
                continue
        return None

    @staticmethod
    def datetime_format(dt: datetime.datetime, fmt: str = datetime_formats_ymdhms_standard) -> str:
        """Get string representation of a datetime"""
        return dt.strftime(fmt)

    @staticmethod
    def datetime_str_reformat(dt_str: str, dt_str_fmt: str, new_fmt: str = datetime_formats_ymdhms_standard) -> str:
        """Convert datetime to date string"""
        datetime_obj = datetime.datetime.strptime(dt_str, dt_str_fmt)
        return CoreUtilities.datetime_format(datetime_obj, new_fmt)