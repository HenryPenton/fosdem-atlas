"""Tests for the FOSDEM schedule scraper."""

from datetime import datetime

from src.adapters.scraper.fosdem_scraper import FosdemScheduleFetcher

SAMPLE_XML = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<schedule>
  <persons>
    <person id="p1">
      <name>Alice</name>
      <biography>&lt;p&gt;Alice is a kernel developer.&lt;/p&gt;</biography>
    </person>
    <person id="p2">
      <name>Bob</name>
      <biography></biography>
    </person>
  </persons>
  <day index="1" date="2026-02-07">
    <room name="Janson">
      <event id="101">
        <title>Welcome to FOSDEM</title>
        <subtitle>Opening session</subtitle>
        <abstract>The annual opening of FOSDEM.</abstract>
        <track>Main</track>
        <start>09:00</start>
        <duration>00:30</duration>
        <persons>
          <person id="p1">Alice</person>
          <person id="p2">Bob</person>
        </persons>
        <links>
          <link href="https://fosdem.org/talk/101">Details</link>
        </links>
      </event>
      <event id="102">
        <title>No Extras</title>
        <subtitle></subtitle>
        <abstract></abstract>
        <track>Main</track>
        <start>10:00</start>
        <duration>01:00</duration>
      </event>
    </room>
  </day>
  <day index="2" date="2026-02-08">
    <room name="K.1.105">
      <event id="201">
        <title>Day Two Talk</title>
        <subtitle/>
        <abstract>A talk on day two.</abstract>
        <track>Testing</track>
        <start>14:30</start>
        <duration>00:45</duration>
      </event>
    </room>
  </day>
</schedule>
"""


class TestFosdemScheduleFetcher:
    def setup_method(self) -> None:
        self.fetcher = FosdemScheduleFetcher()

    def test_parse_event_count(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        assert len(events) == 3

    def test_parse_event_fields(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        e = events[0]
        assert e.id == "101"
        assert e.title == "Welcome to FOSDEM"
        assert e.subtitle == "Opening session"
        assert e.abstract == "The annual opening of FOSDEM."
        assert e.track == "Main"
        assert e.room == "Janson"
        assert e.day == "2026-02-07"
        assert e.duration_minutes == 30
        assert e.start_time == datetime(2026, 2, 7, 9, 0)

    def test_parse_speakers(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        speakers = events[0].speakers
        assert len(speakers) == 2
        assert speakers[0].id == "p1"
        assert speakers[0].name == "Alice"

    def test_parse_speaker_bio(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        speakers = events[0].speakers
        assert speakers[0].bio == "Alice is a kernel developer."
        assert speakers[1].bio == ""

    def test_parse_speaker_bio_strips_html(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        assert "<p>" not in events[0].speakers[0].bio

    def test_parse_links(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        links = events[0].links
        assert len(links) == 1
        assert links[0].href == "https://fosdem.org/talk/101"
        assert links[0].title == "Details"

    def test_parse_empty_subtitle_abstract(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        e = events[1]  # "No Extras"
        assert e.subtitle == ""
        assert e.abstract == ""
        assert e.speakers == []

    def test_parse_duration_one_hour(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        e = events[1]
        assert e.duration_minutes == 60

    def test_parse_duration_45_min(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        e = events[2]
        assert e.duration_minutes == 45

    def test_parse_multi_day(self) -> None:
        events = self.fetcher._parse(SAMPLE_XML)
        days = {e.day for e in events}
        assert days == {"2026-02-07", "2026-02-08"}


class TestParseDuration:
    def test_valid(self) -> None:
        assert FosdemScheduleFetcher._parse_duration("01:30") == 90

    def test_zero(self) -> None:
        assert FosdemScheduleFetcher._parse_duration("00:00") == 0

    def test_empty(self) -> None:
        assert FosdemScheduleFetcher._parse_duration("") == 0

    def test_no_colon(self) -> None:
        assert FosdemScheduleFetcher._parse_duration("90") == 0

    def test_invalid(self) -> None:
        assert FosdemScheduleFetcher._parse_duration("abc:def") == 0


class TestParseDatetime:
    def test_valid(self) -> None:
        result = FosdemScheduleFetcher._parse_datetime("2026-02-07", "10:30")
        assert result == datetime(2026, 2, 7, 10, 30)

    def test_empty_date(self) -> None:
        assert FosdemScheduleFetcher._parse_datetime("", "10:00") == datetime.min

    def test_empty_time(self) -> None:
        assert FosdemScheduleFetcher._parse_datetime("2026-02-07", "") == datetime.min

    def test_invalid_format(self) -> None:
        assert FosdemScheduleFetcher._parse_datetime("bad", "bad") == datetime.min
