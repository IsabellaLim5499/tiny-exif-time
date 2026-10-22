from datetime import datetime, timezone, timedelta
import re


_EXIF_PATTERN = re.compile(
    r"^"
    r"(?P<year>\d{4}):(?P<month>\d{2}):(?P<day>\d{2})"
    r" "
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?P<fraction>\.\d+)?"
    r"(?P<offset>Z|[+-]\d{2}:\d{2})?"
    r"$"
)


class ExifTimeError(ValueError):
    """Raised when an EXIF date-time string cannot be parsed."""


def parse_exif_time(value):
    """Parse an EXIF date-time string into a timezone-aware datetime.

    Accepted format (the one used by EXIF DateTimeOriginal, DateTimeDigitized,
    and DateTime tags):

        YYYY:MM:DD HH:MM:SS[.f][Z|±HH:MM]

    - The date portion uses colons, which is unique to EXIF and not accepted
      by ``datetime.fromisoformat``. We cannot use the stdlib parser directly.
    - A fractional-second component is consumed and applied as microseconds.
    - If a timezone offset (``Z`` or ``±HH:MM``) is present, it is applied.
    - If no timezone is present, the result is returned with a fixed UTC
      offset of zero. This is a deliberate normalization: raw EXIF strings
      almost never carry timezone data, and leaving them naive creates a
      footgun downstream (comparing aware vs naive datetimes raises). This
      makes the return type always ``datetime`` with ``tzinfo`` set.

    Raises:
        ExifTimeError: If the string is not a string, does not match the
            expected format, or has out-of-range values (e.g. month 13).
    """
    if not isinstance(value, str):
        raise ExifTimeError(
            "Expected a string, got {}: {!r}".format(type(value).__name__, value)
        )

    value = value.strip()
    match = _EXIF_PATTERN.match(value)
    if match is None:
        raise ExifTimeError("Unrecognized EXIF time format: {!r}".format(value))

    groups = match.groupdict()

    try:
        year = int(groups["year"])
        month = int(groups["month"])
        day = int(groups["day"])
        hour = int(groups["hour"])
        minute = int(groups["minute"])
        second = int(groups["second"])
    except (ValueError, TypeError) as exc:
        raise ExifTimeError(
            "Invalid integer component in {!r}: {}".format(value, exc)
        ) from exc

    microsecond = 0
    fraction_str = groups.get("fraction")
    if fraction_str:
        # The regex captured '.NNNN'. We need microsecond precision (6 digits).
        # Truncate, do not round — EXIF sub-second data is best-effort.
        try:
            fractional = float(fraction_str)
        except ValueError:
            raise ExifTimeError(
                "Invalid fractional seconds in {!r}".format(value)
        ) from None
        microsecond = int(round(fractional * 1_000_000))
        if microsecond >= 1_000_000:
            microsecond = 999_999

    offset_str = groups.get("offset")
    if offset_str == "Z":
        tzinfo = timezone.utc
    elif offset_str:
        sign = 1 if offset_str[0] == "+" else -1
        try:
            oh = int(offset_str[1:3])
            om = int(offset_str[4:6])
        except ValueError:
            raise ExifTimeError(
                "Invalid offset in {!r}".format(value)
            ) from None
        tzinfo = timezone(sign * timedelta(hours=oh, minutes=om))
    else:
        tzinfo = timezone.utc

    try:
        return datetime(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            second=second,
            microsecond=microsecond,
            tzinfo=tzinfo,
        )
    except ValueError as exc:
        raise ExifTimeError(
            "Out-of-range values in {!r}: {}".format(value, exc)
        ) from exc


def to_iso8601(dt):
    """Convert a datetime to an ISO 8601 string with a ``Z`` suffix when UTC.

    This is a convenience formatter for downstream consumers (JSON, filenames).
    Non-UTC offsets are preserved as ``±HH:MM``. The input must be timezone-aware
    so the output is unambiguous.

    Raises:
        ExifTimeError: If ``dt`` is naive (no ``tzinfo``).
    """
    if not isinstance(dt, datetime):
        raise ExifTimeError(
            "Expected datetime, got {}".format(type(dt).__name__)
        )
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ExifTimeError(
            "Refusing to format a naive datetime; results would be ambiguous."
        )

    if dt.tzinfo.utcoffset(dt) == timedelta(0):
        return dt.replace(tzinfo=None).isoformat() + "Z"
    return dt.isoformat()
