# tiny-exif-time

Parses and normalizes EXIF date-time strings from image metadata into timezone-aware `datetime` objects.

## Usage

```python
from tiny_exif_time import parse_exif_time, to_iso8601, ExifTimeError

dt = parse_exif_time("2023:01:15 14:30:00")
print(dt.isoformat())      # 2023-01-15T14:30:00+00:00
print(to_iso8601(dt))       # 2023-01-15T14:30:00Z

try:
    parse_exif_time("not a date")
except ExifTimeError as e:
    print(e)
```

## Why this exists

Image metadata produced by real cameras uses one of three EXIF date-time formats (`DateTimeOriginal`, `DateTimeDigitized`, `DateTime`). All three share a colon-separated date and space-separated time: `YYYY:MM:DD HH:MM:SS`. Raw EXIF data is text-only, has no native timezone, and cameras rarely populate the `OffsetTime*` tags. This library parses the canonical format (with optional timezone offset) and nothing else. If you need to handle arbitrary date strings, use the standard library's `datetime.fromisoformat` instead.

## Edge cases

Subseconds and timezone offsets are parsed when present. A trailing subsecond fraction with no decimal (a common camera bug) is ignored. Unparseable input raises `ExifTimeError`. Strings with no timezone are returned with an explicit UTC offset of `+00:00` to avoid ambiguity downstream.
