#!/usr/bin/env python3
from __future__ import annotations

import calendar
from collections.abc import Mapping
from datetime import datetime, timezone
from html import unescape
import logging
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any, Optional

from bs4 import BeautifulSoup
import feedparser
import requests

DEFAULT_RSS_URL = "https://www.githubstatus.com/history.rss"
DEFAULT_LAST_CHECK_FILE = ".last_checked"
PUSHOVER_ENDPOINT = "https://api.pushover.net/1/messages.json"

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_check_interval_seconds() -> int:
    return int(os.getenv("CHECK_INTERVAL", "300"))


def get_rss_url() -> str:
    return os.getenv("RSS_URL", DEFAULT_RSS_URL)


def get_last_check_path() -> Path:
    return Path(os.getenv("LAST_CHECK_FILE", DEFAULT_LAST_CHECK_FILE))


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f"{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())

    os.replace(tmp_path, path)


def coerce_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_last_checked_time(path: Path) -> datetime:
    try:
        raw = path.read_text(encoding="utf-8").strip()
        dt = datetime.fromisoformat(raw)
        return coerce_utc(dt)
    except (FileNotFoundError, ValueError, OSError):
        return utc_now()


def save_last_checked_time(path: Path, last_time: Optional[datetime] = None) -> None:
    if last_time is None:
        last_time = utc_now()

    last_time = coerce_utc(last_time)
    atomic_write_text(path, last_time.isoformat())


def entry_field(entry: Any, name: str, default: Any = None) -> Any:
    # feedparser entries are dict-like (Mapping); mocks and other objects may not be.
    if isinstance(entry, Mapping):
        return entry.get(name, default)
    return getattr(entry, name, default)


def entry_published_time(entry: Any) -> Optional[datetime]:
    parsed = getattr(entry, "published_parsed", None) or getattr(
        entry, "updated_parsed", None
    )
    if parsed is None:
        return None

    try:
        ts = calendar.timegm(parsed)
    except Exception:
        return None

    return datetime.fromtimestamp(ts, tz=timezone.utc)


def html_to_text(html_content: str) -> str:
    """Convert HTML content to plain text.

    Uses BeautifulSoup to reliably parse HTML and extract readable text.
    - <p> tags become separated paragraphs (blank line between)
    - <br> tags become line breaks
    - HTML entities are unescaped
    """

    soup = BeautifulSoup(html_content or "", "html.parser")

    # Convert <br> tags into explicit newlines.
    for br in soup.find_all("br"):
        br.replace_with("\n")

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    if paragraphs:
        text = "\n\n".join(paragraphs)
    else:
        text = soup.get_text()

    text = unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Normalize whitespace around line breaks while preserving deliberate breaks.
    text = "\n".join(line.strip() for line in text.splitlines())
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    # Remove spaces before common punctuation introduced by token joining.
    text = re.sub(r"\s+([!?,.:;])", r"\1", text)

    return text.strip()


def get_request_timeout_seconds() -> float:
    return float(os.getenv("REQUEST_TIMEOUT_SECONDS", "5"))


def get_pushover_retry_config() -> tuple[int, float, float]:
    max_attempts = int(os.getenv("PUSHOVER_MAX_ATTEMPTS", "3"))
    backoff_base = float(os.getenv("PUSHOVER_BACKOFF_BASE_SECONDS", "1.0"))
    backoff_max = float(os.getenv("PUSHOVER_BACKOFF_MAX_SECONDS", "30.0"))
    return max_attempts, backoff_base, backoff_max


def send_pushover_notification(
    *,
    session: requests.Session,
    token: str,
    user: str,
    title: str,
    message: str,
    url: str,
) -> None:
    payload = {
        "token": token,
        "user": user,
        "message": message,
        "title": title,
        "url": url,
    }

    max_attempts, backoff_base, backoff_max = get_pushover_retry_config()
    timeout = get_request_timeout_seconds()

    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.post(PUSHOVER_ENDPOINT, data=payload, timeout=timeout)
            resp.raise_for_status()
            return
        except requests.HTTPError as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            body = getattr(getattr(exc, "response", None), "text", "") or ""
            logger.error(
                "Pushover request failed (status=%s): %s",
                status,
                body.strip()[:1000],
            )

            is_transient = status == 429 or (
                isinstance(status, int) and 500 <= status <= 599
            )
            if (not is_transient) or attempt >= max_attempts:
                raise

        except requests.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            # Treat network/timeouts as transient.
            is_transient = (
                status is None
                or status == 429
                or (isinstance(status, int) and 500 <= status <= 599)
            )
            if (not is_transient) or attempt >= max_attempts:
                logger.exception(
                    "Pushover request failed permanently after %s attempt(s)",
                    attempt,
                )
                raise

        sleep_seconds = min(backoff_base * (2 ** (attempt - 1)), backoff_max)
        logger.warning(
            "Pushover request failed (attempt %s/%s). Retrying in %.1fs",
            attempt,
            max_attempts,
            sleep_seconds,
        )
        time.sleep(sleep_seconds)


def check_feed(
    *,
    session: requests.Session,
    token: str,
    user: str,
    rss_url: Optional[str] = None,
    last_check_path: Optional[Path] = None,
) -> None:
    if rss_url is None:
        rss_url = get_rss_url()
    if last_check_path is None:
        last_check_path = get_last_check_path()

    feed = feedparser.parse(rss_url)
    if getattr(feed, "bozo", False):
        logger.warning("Feed parse error: %s", getattr(feed, "bozo_exception", None))

    entries = getattr(feed, "entries", []) or []

    # First run: initialize last-checked to newest entry without sending notifications.
    if not last_check_path.exists():
        newest: Optional[datetime] = None
        for entry in entries:
            published = entry_published_time(entry)
            if published is None:
                continue
            newest = published if newest is None else max(newest, published)

        initial_time = newest or utc_now()
        save_last_checked_time(last_check_path, initial_time)
        logger.info(
            "First run: initialized last-checked to %s (no notifications sent)",
            initial_time.isoformat(),
        )
        return

    last_checked = get_last_checked_time(last_check_path)
    new_last_checked = last_checked

    dated_entries: list[tuple[datetime, Any]] = []
    for entry in entries:
        published = entry_published_time(entry)
        if published is None:
            logger.debug(
                "Skipping entry without published time: %s",
                entry_field(entry, "title", "<no title>"),
            )
            continue
        dated_entries.append((published, entry))

    dated_entries.sort(key=lambda t: t[0])

    for published_time, entry in dated_entries:
        if published_time <= last_checked:
            continue

        title = str(entry_field(entry, "title", "GitHub Status"))
        description = str(entry_field(entry, "description", ""))
        link = str(entry_field(entry, "link", ""))

        send_pushover_notification(
            session=session,
            token=token,
            user=user,
            title=title,
            message=html_to_text(description),
            url=link,
        )

        logger.info("Sent notification: %s", title)
        if published_time > new_last_checked:
            new_last_checked = published_time

    save_last_checked_time(last_check_path, new_last_checked)


def main() -> None:
    configure_logging()

    token = require_env("PUSHOVER_TOKEN")
    user = require_env("PUSHOVER_USER")

    interval_seconds = get_check_interval_seconds()
    logger.info(
        "Starting; check interval=%ss rss_url=%s", interval_seconds, get_rss_url()
    )

    session = requests.Session()

    try:
        while True:
            try:
                check_feed(session=session, token=token, user=user)
            except Exception:
                logger.exception("check_feed failed")

            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
