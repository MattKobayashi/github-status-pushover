#!/usr/bin/env python3
import os
import time
from datetime import datetime, timedelta
import feedparser
import requests
import re
from html import unescape

# Configuration
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # Default 5 minutes
PUSHOVER_TOKEN = os.environ['PUSHOVER_TOKEN']
PUSHOVER_USER = os.environ['PUSHOVER_USER']
RSS_URL = 'https://www.githubstatus.com/history.rss'
LAST_CHECK_FILE = '.last_checked'


def html_to_text(html_content):
    """Convert HTML content to plain text by stripping tags and unescaping entities."""
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


def save_last_checked_time():
    """
    Saves the current datetime to a file in ISO format.

    The function writes the current datetime in ISO format to the file specified by LAST_CHECK_FILE.
    This timestamp can be used to track when the last check was performed.

    Returns:
        None
    """
    with open(LAST_CHECK_FILE, 'w', encoding='utf-8') as f:
        f.write(datetime.now().isoformat())


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
    last_checked = get_last_checked_time()
    feed = feedparser.parse(RSS_URL)

    for entry in reversed(feed.entries):  # Process oldest first
        published_time = datetime(*entry.published_parsed[:6])
        if published_time > last_checked:
            send_pushover_notification(
                title=entry.title,
                message=html_to_text(entry.description),
                url=entry.link
            )

    save_last_checked_time()


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
