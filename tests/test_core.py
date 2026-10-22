import unittest
from datetime import datetime, timezone, timedelta

from tiny_exif_time.core import parse_exif_time, to_iso8601, ExifTimeError


class TestParseExifTime(unittest.TestCase):

    def test_basic_format(self):
        dt = parse_exif_time("2023:01:15 14:30:00")
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 15)
        self.assertEqual(dt.hour, 14)
        self.assertEqual(dt.minute, 30)
        self.assertEqual(dt.second, 0)
        self.assertEqual(dt.microsecond, 0)
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_trailing_whitespace(self):
        dt = parse_exif_time("  2023:01:15 14:30:00  ")
        self.assertEqual(dt.hour, 14)

    def test_with_z_suffix(self):
        dt = parse_exif_time("2023:01:15 14:30:00Z")
        self.assertEqual(dt.tzinfo, timezone.utc)

    def test_with_positive_offset(self):
        dt = parse_exif_time("2023:01:15 14:30:00+05:30")
        self.assertEqual(dt.utcoffset(), timedelta(hours=5, minutes=30))

    def test_with_negative_offset(self):
        dt = parse_exif_time("2023:01:15 14:30:00-08:00")
        self.assertEqual(dt.utcoffset(), timedelta(hours=-8))

    def test_subseconds_truncated_to_microseconds(self):
        dt = parse_exif_time("2023:01:15 14:30:00.123456")
        self.assertEqual(dt.microsecond, 123456)

    def test_subseconds_short(self):
        dt = parse_exif_time("2023:01:15 14:30:00.5")
        # 0.5 seconds = 500000 microseconds
        self.assertEqual(dt.microsecond, 500000)

    def test_invalid_type(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_time(20230115)

    def test_invalid_format_not_a_date(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_time("not a date")

    def test_invalid_format_dash_separated(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_time("2023-01-15 14:30:00")

    def test_invalid_format_no_space(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_time("2023:01:1514:30:00")

    def test_out_of_range_month(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_time("2023:13:01 14:30:00")

    def test_out_of_range_day(self):
        with self.assertRaises(ExifTimeError):
            parse_exif_time("2023:02:30 14:30:00")

    def test_no_timezone_is_utc(self):
        dt = parse_exif_time("2023:01:15 14:30:00")
        self.assertIsNotNone(dt.tzinfo)
        self.assertEqual(dt.utcoffset(), timedelta(0))


class TestToIso8601(unittest.TestCase):

    def test_utc_uses_z(self):
        dt = datetime(2023, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(to_iso8601(dt), "2023-01-15T14:30:00Z")

    def test_microseconds_included(self):
        dt = datetime(2023, 1, 15, 14, 30, 0, 123456, tzinfo=timezone.utc)
        self.assertEqual(to_iso8601(dt), "2023-01-15T14:30:00.123456Z")

    def test_non_utc_offset_preserved(self):
        tz = timezone(timedelta(hours=-5))
        dt = datetime(2023, 1, 15, 14, 30, 0, tzinfo=tz)
        self.assertEqual(to_iso8601(dt), "2023-01-15T14:30:00-05:00")

    def test_naive_datetime_raises(self):
        dt = datetime(2023, 1, 15, 14, 30, 0)
        with self.assertRaises(ExifTimeError):
            to_iso8601(dt)

    def test_non_datetime_raises(self):
        with self.assertRaises(ExifTimeError):
            to_iso8601("2023-01-15")


if __name__ == "__main__":
    unittest.main()
