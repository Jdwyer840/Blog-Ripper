import datetime
import hashlib
import typing
import zoneinfo


class CoreUtilities:

    @staticmethod
    def read_file(file_path):
        with open(file_path, 'r') as file:
            file.read()

    @staticmethod
    def datetime_zoneinfo(tz: typing.Union[str, zoneinfo.ZoneInfo]) -> zoneinfo.ZoneInfo:
        """Helper method to get zoneinfo from the specified timezone string"""
        return zoneinfo.ZoneInfo(tz) if isinstance(tz, str) else tz

    @staticmethod
    def datetime_tz_aware(value: str, tz: typing.Any = datetime.timezone.utc) -> datetime.datetime:
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