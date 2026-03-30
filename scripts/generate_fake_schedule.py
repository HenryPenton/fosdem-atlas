#!/usr/bin/env python3
"""Generate a fake two-day FOSDEM Pentabarf XML schedule for local development.

Day 1 = today's date (the "Saturday" equivalent).
Day 2 = tomorrow's date (the "Sunday" equivalent).

Output: fake_schedule.xml in the project root.
"""

from __future__ import annotations

import textwrap
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from xml.dom import minidom
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Static fake data
# ---------------------------------------------------------------------------

SPEAKERS = [
    {
        "id": "101",
        "name": "Alice Müller",
        "bio": "Alice is a principal engineer at Quantum Systems and has been contributing to open-source infrastructure tools for over a decade.",
    },
    {
        "id": "102",
        "name": "Bob Dupont",
        "bio": "Bob works on container runtime security at CloudCo and is a maintainer of several CNCF projects.",
    },
    {
        "id": "103",
        "name": "Carla Santos",
        "bio": "Carla is a database researcher specialising in analytical query engines and the author of three books on distributed systems.",
    },
    {
        "id": "104",
        "name": "David Kim",
        "bio": "David is a cryptography engineer who contributes to OpenSSL and has spoken at DEF CON and Black Hat.",
    },
    {
        "id": "105",
        "name": "Eva Johansson",
        "bio": "Eva is a Python core developer and the creator of a widely used async web framework.",
    },
    {
        "id": "106",
        "name": "Frank Osei",
        "bio": "Frank is a site-reliability engineer with 15 years of experience running large-scale Kubernetes clusters.",
    },
    {
        "id": "107",
        "name": "Grace Li",
        "bio": "Grace researches supply-chain security and has authored several CVEs in popular package managers.",
    },
    {
        "id": "108",
        "name": "Hamid Reza",
        "bio": "Hamid is a DuckDB contributor and data-engineering lead at AnalyticsCo.",
    },
    {
        "id": "109",
        "name": "Ingrid Bakker",
        "bio": "Ingrid is an accessibility advocate and front-end engineer passionate about inclusive open-source software.",
    },
    {
        "id": "110",
        "name": "José Martínez",
        "bio": "José is a Linux kernel developer specialising in storage subsystems and file-system performance.",
    },
]

# Each event: title, subtitle, track, room, start (HH:MM), duration (HH:MM), speaker_ids, link
EVENTS_DAY1 = [
    {
        "id": "1001",
        "title": "Opening Keynote: The State of Open Source",
        "subtitle": "Welcome to this year's conference",
        "abstract": textwrap.dedent("""\
            <p>A broad look at the past year in open-source software: licensing shifts,
            AI-generated code controversies, and the growing importance of supply-chain
            security. This talk sets the stage for two days of lightning-fast knowledge
            sharing across every corner of the ecosystem.</p>"""),
        "track": "Keynotes",
        "room": "Janson",
        "start": "09:00",
        "duration": "01:00",
        "speaker_ids": ["101"],
        "links": [{"href": "https://example.fosdem/keynote-slides", "title": "Slides"}],
    },
    {
        "id": "1002",
        "title": "Python Type System Deep Dive",
        "subtitle": "From PEP 484 to PEP 742",
        "abstract": textwrap.dedent("""\
            <p>We trace the evolution of Python's type system from its tentative beginning
            in PEP 484 through to the latest improvements in 3.13. Practical patterns for
            writing maintainable, fully annotated codebases are demonstrated with real
            project examples.</p>"""),
        "track": "Python",
        "room": "K.1.105 (La Fontaine)",
        "start": "10:00",
        "duration": "00:45",
        "speaker_ids": ["105"],
        "links": [{"href": "https://example.fosdem/python-types", "title": "Repository"}],
    },
    {
        "id": "1003",
        "title": "Hardening Container Images at Scale",
        "subtitle": "Distroless, SBOMs, and attestation",
        "abstract": textwrap.dedent("""\
            <p>This session covers a battle-tested pipeline for producing minimal,
            signed container images with full SBOM provenance. Topics include distroless
            base images, Sigstore cosign, and integrating Grype into CI.</p>"""),
        "track": "Containers",
        "room": "H.2215 (Ferrer)",
        "start": "10:00",
        "duration": "00:30",
        "speaker_ids": ["102"],
        "links": [{"href": "https://example.fosdem/containers-hardening", "title": "Slides"}],
    },
    {
        "id": "1004",
        "title": "DuckDB: OLAP on a Laptop",
        "subtitle": "Analytical queries without a cluster",
        "abstract": textwrap.dedent("""\
            <p>DuckDB brings columnar, vectorised query execution to single-machine
            workloads. This talk compares performance against Spark for common ETL
            patterns and shows how to integrate DuckDB into Python and Go services.</p>"""),
        "track": "Databases",
        "room": "UA2.114 (Leuven)",
        "start": "10:00",
        "duration": "00:45",
        "speaker_ids": ["108"],
        "links": [{"href": "https://duckdb.org", "title": "DuckDB website"}],
    },
    {
        "id": "1005",
        "title": "Supply-Chain Attacks: What We Learned",
        "subtitle": "Lessons from the XZ Utils backdoor",
        "abstract": textwrap.dedent("""\
            <p>A detailed post-mortem of the XZ Utils backdoor and what it reveals about
            the trust assumptions baked into open-source maintenance. We propose concrete
            countermeasures for project maintainers and downstream distributors.</p>"""),
        "track": "Security",
        "room": "Janson",
        "start": "10:30",
        "duration": "00:45",
        "speaker_ids": ["107"],
        "links": [
            {"href": "https://example.fosdem/xz-postmortem", "title": "Write-up"},
            {"href": "https://example.fosdem/xz-slides", "title": "Slides"},
        ],
    },
    {
        "id": "1006",
        "title": "Async Python: Beyond asyncio",
        "subtitle": "Structured concurrency with anyio and trio",
        "abstract": textwrap.dedent("""\
            <p>asyncio is powerful but error-prone. This talk introduces structured
            concurrency as a safer mental model and demonstrates how anyio lets you
            write portable async code that works on multiple event loop backends.</p>"""),
        "track": "Python",
        "room": "K.1.105 (La Fontaine)",
        "start": "11:00",
        "duration": "00:30",
        "speaker_ids": ["105"],
        "links": [],
    },
    {
        "id": "1007",
        "title": "Zero-Trust Networking in Practice",
        "subtitle": "mTLS, SPIFFE, and service mesh",
        "abstract": textwrap.dedent("""\
            <p>We walk through a reference architecture for mutual TLS between
            microservices using SPIFFE/SPIRE for identity. Attendees will learn how
            to rotate certificates automatically and audit inter-service traffic.</p>"""),
        "track": "Security",
        "room": "H.2215 (Ferrer)",
        "start": "11:00",
        "duration": "00:45",
        "speaker_ids": ["104"],
        "links": [{"href": "https://spiffe.io", "title": "SPIFFE project"}],
    },
    {
        "id": "1008",
        "title": "Modern Linux Storage Internals",
        "subtitle": "io_uring, NVMe, and the block layer",
        "abstract": textwrap.dedent("""\
            <p>A guided tour through the Linux IO stack from VFS to NVMe. We explore
            io_uring's completion model, compare it with traditional epoll-based async
            IO, and examine tuning knobs for high-throughput storage workloads.</p>"""),
        "track": "Kernel",
        "room": "UA2.114 (Leuven)",
        "start": "11:00",
        "duration": "01:00",
        "speaker_ids": ["110"],
        "links": [],
    },
    {
        "id": "1009",
        "title": "Kubernetes Resource Management at Scale",
        "subtitle": "QoS, LimitRanges, and vertical pod autoscaling",
        "abstract": textwrap.dedent("""\
            <p>Running tens of thousands of pods requires deliberate resource management.
            This talk covers QoS classes, LimitRange policies, the Kubernetes Vertical
            Pod Autoscaler, and hard lessons from running large multi-tenant clusters.</p>"""),
        "track": "Containers",
        "room": "H.2215 (Ferrer)",
        "start": "12:00",
        "duration": "00:45",
        "speaker_ids": ["106"],
        "links": [{"href": "https://example.fosdem/k8s-resources", "title": "Repository"}],
    },
    {
        "id": "1010",
        "title": "Accessibility in Open Source Projects",
        "subtitle": "Making your tooling usable by everyone",
        "abstract": textwrap.dedent("""\
            <p>Free software should be free for everyone. This talk audits common
            developer tooling for accessibility failures, shows quick wins using axe-core
            and screen-reader testing, and explains how to embed a11y checks in CI.</p>"""),
        "track": "Open Source",
        "room": "K.1.105 (La Fontaine)",
        "start": "12:00",
        "duration": "00:30",
        "speaker_ids": ["109"],
        "links": [{"href": "https://example.fosdem/a11y-talk", "title": "Slides"}],
    },
]

EVENTS_DAY2 = [
    {
        "id": "2001",
        "title": "Closing Keynote Preview: What's Next?",
        "subtitle": "Trends shaping the next five years",
        "abstract": textwrap.dedent("""\
            <p>A speculative but grounded look at where open-source software is headed:
            formal verification entering mainstream toolchains, the post-cloud era of
            local-first applications, and what AI actually means for software maintenance.</p>"""),
        "track": "Keynotes",
        "room": "Janson",
        "start": "09:00",
        "duration": "01:00",
        "speaker_ids": ["103"],
        "links": [],
    },
    {
        "id": "2002",
        "title": "Writing Correct Python with Hypothesis",
        "subtitle": "Property-based testing in practice",
        "abstract": textwrap.dedent("""\
            <p>Unit tests check examples; property-based tests check invariants.
            This session teaches the Hypothesis library from first principles, shows
            strategies for common data types, and demonstrates finding real bugs in
            production code during the live demo.</p>"""),
        "track": "Python",
        "room": "K.1.105 (La Fontaine)",
        "start": "10:00",
        "duration": "00:45",
        "speaker_ids": ["105"],
        "links": [{"href": "https://hypothesis.works", "title": "Hypothesis docs"}],
    },
    {
        "id": "2003",
        "title": "Post-Quantum Cryptography Migration",
        "subtitle": "Preparing your systems for Q-Day",
        "abstract": textwrap.dedent("""\
            <p>NIST's post-quantum standards are finalised. This talk explains the maths
            behind CRYSTALS-Kyber and CRYSTALS-Dilithium at an accessible level, then
            shows practical migration paths for TLS, SSH, and code-signing workflows.</p>"""),
        "track": "Security",
        "room": "H.2215 (Ferrer)",
        "start": "10:00",
        "duration": "01:00",
        "speaker_ids": ["104"],
        "links": [
            {"href": "https://csrc.nist.gov/pqc", "title": "NIST PQC project"},
        ],
    },
    {
        "id": "2004",
        "title": "Columnar Storage Formats Compared",
        "subtitle": "Parquet, ORC, Lance, and beyond",
        "abstract": textwrap.dedent("""\
            <p>A rigorous benchmark comparing columnar file formats across scan speed,
            compression ratio, and write throughput. We cover Parquet v2, ORC, the new
            Lance format for ML workloads, and Apache Iceberg table evolution.</p>"""),
        "track": "Databases",
        "room": "UA2.114 (Leuven)",
        "start": "10:00",
        "duration": "00:45",
        "speaker_ids": ["108", "103"],
        "links": [
            {"href": "https://example.fosdem/storage-formats", "title": "Benchmark repository"}
        ],
    },
    {
        "id": "2005",
        "title": "eBPF for Application Developers",
        "subtitle": "Observability without instrumentation",
        "abstract": textwrap.dedent("""\
            <p>eBPF lets you attach programs to kernel hooks without modifying application
            code. This talk introduces libbpf and shows how to build tracing tools that
            capture latency histograms, syscall counts, and network flows in production.</p>"""),
        "track": "Kernel",
        "room": "Janson",
        "start": "10:30",
        "duration": "00:45",
        "speaker_ids": ["110"],
        "links": [{"href": "https://ebpf.io", "title": "eBPF foundation"}],
    },
    {
        "id": "2006",
        "title": "GitOps at the Edge",
        "subtitle": "Fleet management for constrained environments",
        "abstract": textwrap.dedent("""\
            <p>Managing thousands of edge nodes with GitOps tooling requires rethinking
            pull intervals, offline tolerance, and partial connectivity. This talk walks
            through a Fleet architecture for 5 000 Raspberry Pi nodes in retail stores.</p>"""),
        "track": "Containers",
        "room": "H.2215 (Ferrer)",
        "start": "11:00",
        "duration": "00:30",
        "speaker_ids": ["106"],
        "links": [],
    },
    {
        "id": "2007",
        "title": "Open Source Sustainability Models",
        "subtitle": "Beyond GitHub Sponsors",
        "abstract": textwrap.dedent("""\
            <p>We survey funding models that have worked for mid-sized open-source
            projects: dual licensing, open-core, foundation membership, and
            paid support. Case studies from five projects with annual revenues over
            $1 M are examined.</p>"""),
        "track": "Open Source",
        "room": "K.1.105 (La Fontaine)",
        "start": "11:00",
        "duration": "00:45",
        "speaker_ids": ["101"],
        "links": [{"href": "https://example.fosdem/oss-sustainability", "title": "Slides"}],
    },
    {
        "id": "2008",
        "title": "FastAPI in Production",
        "subtitle": "Lessons from three years in the wild",
        "abstract": textwrap.dedent("""\
            <p>FastAPI has become the go-to Python web framework for API-heavy services.
            This talk shares hard-won lessons: dependency injection pitfalls, background
            task gotchas, Pydantic v2 migration pain, and profiling async endpoints
            under real traffic.</p>"""),
        "track": "Python",
        "room": "UA2.114 (Leuven)",
        "start": "11:00",
        "duration": "00:30",
        "speaker_ids": ["105"],
        "links": [],
    },
    {
        "id": "2009",
        "title": "Reproducible Builds: State of the Art",
        "subtitle": "From compiler flags to attestation",
        "abstract": textwrap.dedent("""\
            <p>Reproducible builds close the gap between source code and distributed
            binaries. This talk covers toolchain hardening, SOURCE_DATE_EPOCH, in-toto
            attestations, and the Reproducible Builds project's current status across
            Debian, Arch, NixOS, and Gentoo.</p>"""),
        "track": "Security",
        "room": "K.1.105 (La Fontaine)",
        "start": "12:00",
        "duration": "00:45",
        "speaker_ids": ["107"],
        "links": [
            {"href": "https://reproducible-builds.org", "title": "Reproducible Builds project"}
        ],
    },
    {
        "id": "2010",
        "title": "Closing Ceremony",
        "subtitle": "Thank you and see you next year",
        "abstract": textwrap.dedent("""\
            <p>The FOSDEM organisers thank all speakers, volunteers, and attendees.
            Statistics from this year's event are presented together with a short
            preview of what to expect from FOSDEM next year.</p>"""),
        "track": "Keynotes",
        "room": "Janson",
        "start": "17:00",
        "duration": "00:30",
        "speaker_ids": ["101"],
        "links": [],
    },
]


# ---------------------------------------------------------------------------
# XML builder
# ---------------------------------------------------------------------------


def _sub(parent: ET.Element, tag: str, text: str = "") -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def build_schedule(day1: date, day2: date) -> ET.Element:
    root = ET.Element("schedule")

    # Conference section
    conf = ET.SubElement(root, "conference")
    _sub(conf, "title", "FOSDEM (fake)")
    _sub(conf, "subtitle", "Generated for local development")
    _sub(conf, "venue", "ULB (Université Libre de Bruxelles)")
    _sub(conf, "city", "Brussels")
    _sub(conf, "start", day1.isoformat())
    _sub(conf, "end", day2.isoformat())
    _sub(conf, "days", "2")
    _sub(conf, "day_change", "09:00")
    _sub(conf, "timeslot_duration", "00:30")

    # Persons section (top-level, used for bios)
    persons_el = ET.SubElement(root, "persons")
    for speaker in SPEAKERS:
        p = ET.SubElement(persons_el, "person", id=speaker["id"])
        _sub(p, "name", speaker["name"])
        _sub(p, "biography", speaker["bio"])

    speaker_map = {s["id"]: s["name"] for s in SPEAKERS}

    def add_day(index: int, day_date: date, events: list[Any]) -> None:
        day_el = ET.SubElement(root, "day", index=str(index), date=day_date.isoformat())

        # Group events by room
        rooms: dict[str, list[Any]] = {}
        for ev in events:
            rooms.setdefault(ev["room"], []).append(ev)

        for room_name, room_events in rooms.items():
            room_el = ET.SubElement(day_el, "room", name=room_name)
            for ev in room_events:
                event_el = ET.SubElement(room_el, "event", id=ev["id"])
                _sub(event_el, "start", ev["start"])
                _sub(event_el, "duration", ev["duration"])
                _sub(event_el, "room", room_name)
                _sub(event_el, "title", ev["title"])
                _sub(event_el, "subtitle", ev["subtitle"])
                _sub(event_el, "track", ev["track"])
                _sub(event_el, "type", "talk")
                _sub(event_el, "language", "English")
                abstract_el = ET.SubElement(event_el, "abstract")
                abstract_el.text = ev["abstract"]

                persons_sub = ET.SubElement(event_el, "persons")
                for sid in ev["speaker_ids"]:
                    p_el = ET.SubElement(persons_sub, "person", id=sid)
                    p_el.text = speaker_map.get(sid, "Unknown Speaker")

                links_el = ET.SubElement(event_el, "links")
                for lk in ev.get("links", []):
                    lk_el = ET.SubElement(links_el, "link", href=lk["href"])
                    lk_el.text = lk["title"]

    add_day(1, day1, EVENTS_DAY1)
    add_day(2, day2, EVENTS_DAY2)

    return root


def prettify(root: ET.Element) -> str:
    rough = ET.tostring(root, encoding="unicode")
    reparsed = minidom.parseString(rough)
    return reparsed.toprettyxml(indent="  ", encoding=None)


def main() -> None:
    today = date.today()
    tomorrow = today + timedelta(days=1)

    root = build_schedule(today, tomorrow)
    xml_str = prettify(root)

    # minidom prepends an XML declaration — keep it but ensure UTF-8 is stated
    if not xml_str.startswith("<?xml"):
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

    out_path = Path(__file__).parent.parent / "fake_schedule.xml"
    out_path.write_text(xml_str, encoding="utf-8")
    print(f"Written {out_path}  (day 1: {today}, day 2: {tomorrow})")


if __name__ == "__main__":
    main()
