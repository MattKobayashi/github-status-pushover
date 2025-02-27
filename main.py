import os
import time
import feedparser
import requests
from datetime import datetime, timedelta

# Configuration
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))  # Default 5 minutes
PUSHOVER_TOKEN = os.environ['PUSHOVER_TOKEN']
PUSHOVER_USER = os.environ['PUSHOVER_USER']
RSS_URL = 'https://www.githubstatus.com/history.rss'
LAST_CHECK_FILE = '.last_checked'

def send_pushover_notification(title, message, url):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message,
            "title": title,
            "url": url
        }
    )

def get_last_checked_time():
    try:
        with open(LAST_CHECK_FILE, 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    except FileNotFoundError:
        return datetime.now() - timedelta(minutes=60)

def save_last_checked_time():
    with open(LAST_CHECK_FILE, 'w') as f:
        f.write(datetime.now().isoformat())

def check_feed():
    last_checked = get_last_checked_time()
    feed = feedparser.parse(RSS_URL)
    
    for entry in reversed(feed.entries):  # Process oldest first
        published_time = datetime(*entry.published_parsed[:6])
        if published_time > last_checked:
            send_pushover_notification(
                title=entry.title,
                message=entry.description,
                url=entry.link
            )
    
    save_last_checked_time()

def main():
    while True:
        check_feed()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
