from __future__ import annotations

import asyncio
import html
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from src.geo.hyderabad import LOCALITIES

PUBLISHER_SUFFIX_PATTERN = re.compile(r"\s+-\s+[^-]+$")


@dataclass(frozen=True)
class CrawlTarget:
    url: str
    platform: str


HYDERABAD_QUERIES = (
    "Hyderabad civic issue",
    "Hyderabad GHMC complaint",
    "Hyderabad pothole road damage",
    "Hyderabad bad roads traffic civic",
    "Hyderabad sewage overflow complaint GHMC",
    "Hyderabad drainage problem",
    "Hyderabad nala overflow",
    "Hyderabad water supply disruption",
    "Hyderabad drinking water problem",
    "Hyderabad water leakage",
    "Hyderabad street light outage",
    "Hyderabad power cut civic issue",
    "Hyderabad garbage collection issue GHMC",
    "Hyderabad waste dumping",
    "Hyderabad waterlogging monsoon drain",
    "Hyderabad flood prone areas",
    "Hyderabad road repair complaint",
    "Hyderabad public safety traffic issue",
    "Hyderabad encroachment civic issue",
    "Hyderabad lake pollution",
    "Hyderabad footpath encroachment",
    "Hyderabad construction debris",
)

CIVIC_KEYWORDS = (
    "pothole",
    "road",
    "sewage",
    "sewer",
    "drain",
    "drainage",
    "garbage",
    "waste",
    "waterlogging",
    "water supply",
    "drinking water",
    "street light",
    "streetlight",
    "traffic",
    "manhole",
    "ghmc",
    "hmwssb",
    "power cut",
    "electricity",
    "outage",
    "pollution",
    "lake",
    "footpath",
    "encroachment",
    "debris",
    "flood",
    "flooding",
    "nala",
    "civic",
    "complaint",
    "public safety",
)

GRIEVANCE_KEYWORDS = (
    "accident fears",
    "choke",
    "crisis",
    "damage",
    "dark",
    "disrupt",
    "dump",
    "failure",
    "flood",
    "garbage",
    "hotspot",
    "issue",
    "leakage",
    "overflow",
    "pothole",
    "sewage",
    "struggles",
    "waste pile",
    "waterlogging",
    "woes",
    "problem",
    "problems",
    "complaint",
    "complaints",
    "concern",
    "concerns",
    "shortage",
    "contamination",
    "pollution",
    "delay",
    "delayed",
    "repair",
    "repairs",
    "restoration",
    "maintenance",
    "encroachment",
    "debris",
    "overflowing",
    "stagnant",
    "disrupted",
    "disruption",
    "outage",
)

EXCLUDED_TOPICS = (
    "arrest",
    "blazing through",
    "go-kart",
    "praises hyderabad roads",
    "promises",
    "roadmap",
    "traffic-free",
    "election",
    "campaign",
    "manifesto",
    "stock market",
    "movie",
    "cricket",
    "celebrity",
)

SCOPE_NOISE_TERMS = (
    "hyderabad mail",
    "hyderabad news",
)

CATEGORY_KEYWORDS = {
    "Drainage": ("sewage", "sewer", "drain", "drainage", "manhole", "nala"),
    "Roads": ("pothole", "road", "repair", "flyover", "debris"),
    "Water": ("water supply", "drinking water", "low pressure", "water leakage", "hmwssb"),
    "Sanitation": ("garbage", "waste", "sanitation", "trash"),
    "Street Lighting": ("street light", "streetlight", "lighting outage"),
    "Power": ("power cut", "electricity", "power outage"),
    "Traffic & Public Safety": ("traffic", "accident", "unsafe", "public safety"),
    "Urban Infrastructure": ("footpath", "encroachment", "flood", "waterlogging", "lake", "pollution"),
}


def build_default_targets() -> list[CrawlTarget]:
    return [
        CrawlTarget(
            url=(
                "https://news.google.com/rss/search?q="
                f"{quote(query + ' when:90d')}"
                "&hl=en-IN&gl=IN&ceid=IN:en"
            ),
            platform="google_news",
        )
        for query in HYDERABAD_QUERIES
    ]


def _platform_from_url(url: str) -> str:
    hostname = urlparse(url).hostname or ""
    if "reddit.com" in hostname:
        return "reddit"
    if "news.google.com" in hostname:
        return "google_news"
    if "thehindu.com" in hostname or "telanganatoday.com" in hostname:
        return "news"
    return "web"


def _strip_markup(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_publisher_suffix(title: str) -> str:
    return PUBLISHER_SUFFIX_PATTERN.sub("", title).strip()


def _parse_date(value: str | None) -> str:
    if not value:
        return date.today().isoformat()
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.date().isoformat()
    except (TypeError, ValueError):
        pass

    for date_format in ("%Y-%m-%d", "%d %b %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    return date.today().isoformat()


def _fetch_text(url: str, retries: int = 3, delay_seconds: float = 1.5) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Accept-Language": "en-IN,en;q=0.9",
        },
    )
    for attempt in range(1, retries + 1):
        try:
            with urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except (OSError, URLError):
            if attempt == retries:
                return ""
            time.sleep(delay_seconds * attempt)
    return ""


def _find_text(element: ElementTree.Element, *names: str) -> str:
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return _strip_markup(found.text)
    return ""


def _parse_rss(xml_text: str) -> list[dict[str, str]]:
    if not xml_text:
        return []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return []

    entries: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        entries.append(
            {
                "title": _find_text(item, "title"),
                "description": _find_text(item, "description"),
                "link": _find_text(item, "link"),
                "published": _find_text(item, "pubDate"),
            }
        )

    if entries:
        return entries

    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", namespace):
        link = ""
        link_element = entry.find("atom:link", namespace)
        if link_element is not None:
            link = str(link_element.attrib.get("href") or "")
        entries.append(
            {
                "title": _find_text(entry, "{http://www.w3.org/2005/Atom}title"),
                "description": _find_text(entry, "{http://www.w3.org/2005/Atom}summary"),
                "link": link,
                "published": _find_text(
                    entry,
                    "{http://www.w3.org/2005/Atom}published",
                    "{http://www.w3.org/2005/Atom}updated",
                ),
            }
        )
    return entries


def _is_hyderabad_civic_item(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    scope_text = text
    for noise_term in SCOPE_NOISE_TERMS:
        scope_text = scope_text.replace(noise_term, "")
    if "hyderabad" not in scope_text:
        return False
    if any(topic in text for topic in EXCLUDED_TOPICS):
        return False
    return any(keyword in text for keyword in CIVIC_KEYWORDS)


def _extract_area(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    for landmark in sorted(LOCALITIES, key=len, reverse=True):
        if landmark in text:
            return landmark.title()
    return "Hyderabad"


def _classify_category(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return "Uncategorized"


def _score_issue(category: str, title: str, description: str, post_date: str) -> dict[str, float]:
    text = f"{title} {description}".lower()
    severity = 5.0
    if any(word in text for word in ("danger", "accident", "death", "injured", "unsafe", "open manhole")):
        severity = 8.5
    elif category in {"Drainage", "Roads", "Water"}:
        severity = 7.0
    elif category in {"Sanitation", "Street Lighting"}:
        severity = 6.0

    frequency = 6.5 if any(word in text for word in ("residents", "several", "multiple", "again")) else 4.5
    risk = 7.8 if category == "Drainage" and any(word in text for word in ("monsoon", "rain", "waterlogging")) else 5.5
    try:
        age_days = max(0, (date.today() - datetime.strptime(post_date, "%Y-%m-%d").date()).days)
    except ValueError:
        age_days = 0
    duration = min(age_days / 30 * 10, 10)
    return {"S": severity, "F": frequency, "R": risk, "D": round(duration, 2)}


def _entry_to_issue(entry: dict[str, str], platform: str) -> dict[str, Any] | None:
    title = _strip_publisher_suffix(entry["title"])
    description = entry["description"] or title
    if not _is_hyderabad_civic_item(title, description):
        return None

    post_date = _parse_date(entry.get("published"))
    category = _classify_category(title, description)
    scores = _score_issue(category, title, description, post_date)
    area = _extract_area(title, description)
    return {
        "title": title,
        "area": area,
        "category": category,
        "description": description,
        "post_date": post_date,
        "traction_date": post_date,
        "engagement_count": 0,
        "source": platform,
        "source_url": entry.get("link") or "",
        **scores,
    }


async def _scrape_target(target: CrawlTarget) -> list[dict[str, Any]]:
    xml_text = await asyncio.to_thread(_fetch_text, target.url)
    issues = []
    for entry in _parse_rss(xml_text):
        issue = _entry_to_issue(entry, target.platform)
        if issue:
            issues.append(issue)
    return issues


async def scrape_civic_sources_deep(urls: list[str] | None = None) -> list[dict[str, Any]]:
    targets = (
        [CrawlTarget(url=url, platform=_platform_from_url(url)) for url in urls]
        if urls
        else build_default_targets()
    )

    semaphore = asyncio.Semaphore(4)

    async def bounded_scrape(target: CrawlTarget) -> list[dict[str, Any]]:
        async with semaphore:
            return await _scrape_target(target)

    results = await asyncio.gather(*(bounded_scrape(target) for target in targets))

    deduped: dict[str, dict[str, Any]] = {}
    for records in results:
        for record in records:
            key = "|".join(
                [
                    str(record.get("title", "")).lower(),
                    str(record.get("area", "")).lower(),
                    str(record.get("source_url", "")).lower(),
                ]
            )
            deduped[key] = record
    return list(deduped.values())
