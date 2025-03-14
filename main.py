#!/usr/bin/env python3
from datetime import datetime, timedelta
from html import unescape
import os
import re
import time
import feedparser
import requests

# Configuration
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # Default 5 minutes
PUSHOVER_TOKEN = os.environ['PUSHOVER_TOKEN']
PUSHOVER_USER = os.environ['PUSHOVER_USER']
RSS_URL = 'https://www.githubstatus.com/history.rss'
LAST_CHECK_FILE = '.last_checked'


def html_to_text(html_content):
    """Convert HTML content to plain text by converting <p> tags to new paragraphs,
    stripping remaining tags, and unescaping HTML entities."""
    # Convert <br /> and <br/> tags into newline characters.
    html_content = html_content.replace('<br />', '\n').replace('<br/>', '\n')
    # Convert </p> tags into new paragraphs.
    html_content = html_content.replace('</p>', '\n\n')
    # Remove all remaining HTML tags.
    text = re.sub(r'<[^>]+>', '', html_content)
    return unescape(text).strip()


def send_pushover_notification(title, message, url):
    """Send a notification to Pushover service.

    Args:
        title (str): The title of the notification that will appear at the top.
        message (str): The main content/body of the notification message.
        url (str): A URL that will be attached to the notification.

    Returns:
        None

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails or times out after 5 seconds.
    """
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message,
            "title": title,
            "url": url
        },
        timeout=5
    )


def get_last_checked_time():
    """
    Retrieves the timestamp of the last check from a file.

    Returns:
        datetime: The timestamp of the last check. If the file does not exist,
                 returns current time minus 60 minutes.

    This function reads from a file defined by LAST_CHECK_FILE constant. The timestamp
    is expected to be stored in ISO format. If the file cannot be found, it assumes
    the last check was 60 minutes ago from the current time.
    """
    try:
        with open(LAST_CHECK_FILE, 'r', encoding='utf-8') as f:
            return datetime.fromisoformat(f.read().strip())
    except FileNotFoundError:
        return datetime.now() - timedelta(minutes=60)


def save_last_checked_time(last_time=None):
    """
    Saves the current datetime to a file in ISO format.

    The function writes the current datetime in ISO format to the file specified by LAST_CHECK_FILE.
    This timestamp can be used to track when the last check was performed.

    Returns:
        None
    """
    if last_time is None:
        last_time = datetime.now()
    with open(LAST_CHECK_FILE, 'w', encoding='utf-8') as f:
        f.write(last_time.isoformat())


def check_feed():
    """
    Checks the GitHub Status RSS feed for new updates and sends notifications.

    This function retrieves the last checked timestamp, fetches the RSS feed,
    and processes any new entries chronologically. For each new entry that was
    published after the last check time, it sends a Pushover notification.

    The function handles:
    - Reading the last checked time from storage
    - Parsing the RSS feed
    - Processing entries in chronological order (oldest first)
    - Sending notifications for new entries
    - Updating the last checked time

    Returns:
        None
    """
    feed = feedparser.parse(RSS_URL)
    if not os.path.exists(LAST_CHECK_FILE):
        # Initial run: send only the most recent update.
        if feed.entries:
            newest_entry = max(
                feed.entries, key=lambda e: datetime(*e.published_parsed[:6])
            )
            send_pushover_notification(
                title=newest_entry.title,
                message=html_to_text(newest_entry.description),
                url=newest_entry.link
            )
            new_last_checked = datetime(*newest_entry.published_parsed[:6])
        else:
            new_last_checked = datetime.now()
        save_last_checked_time(new_last_checked)
    else:
        last_checked = get_last_checked_time()
        new_last_checked = last_checked
        # Process entries in chronological order (oldest first)
        for entry in sorted(
            feed.entries,
            key=lambda e: datetime(*e.published_parsed[:6])
        ):
            published_time = datetime(*entry.published_parsed[:6])
            if published_time > last_checked:
                send_pushover_notification(
                    title=entry.title,
                    message=html_to_text(entry.description),
                    url=entry.link
                )
                new_last_checked = max(new_last_checked, published_time)
        save_last_checked_time(new_last_checked)


def main():
    """
    Main application loop that continuously monitors GitHub status feed.

    The function runs indefinitely and performs the following:
    1. Checks the GitHub status feed for updates
    2. Sleeps for a configured interval (CHECK_INTERVAL)

    The CHECK_INTERVAL constant should be defined elsewhere in the code
    to determine the frequency of status checks.

    Returns:
        None
    """
    while True:
        check_feed()
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
