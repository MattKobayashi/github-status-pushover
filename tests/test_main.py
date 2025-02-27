#!/usr/bin/env python3
import time
from unittest import mock
from datetime import datetime, timedelta
import pytest
import main


def test_send_pushover_notification_success(mock_requests):
    """Test successful notification sending"""
    main.send_pushover_notification("Test", "Message", "http://example.com")

    mock_requests.post.assert_called_once_with(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": "test_token",
            "user": "test_user",
            "message": "Message",
            "title": "Test",
            "url": "http://example.com"
        },
        timeout=5
    )


def test_send_pushover_notification_failure(mock_requests):
    """Test notification failure propagation"""
    mock_requests.post.side_effect = Exception("API Error")
    with pytest.raises(Exception, match="API Error"):
        main.send_pushover_notification("Test", "Fail", "http://error.com")


def test_get_last_checked_time_file_exists():
    """Test reading stored timestamp"""
    test_time = datetime(2023, 1, 1, 12, 0)
    with mock.patch(
        'builtins.open',
        mock.mock_open(read_data=test_time.isoformat())
    ):
        result = main.get_last_checked_time()
        assert result == test_time


def test_get_last_checked_time_file_missing():
    """Test default timestamp when no file exists"""
    with mock.patch('builtins.open', side_effect=FileNotFoundError):
        result = main.get_last_checked_time()
        assert result < datetime.now() - timedelta(minutes=59)


def test_save_last_checked_time():
    """Test saving current timestamp"""
    test_time = datetime(2023, 1, 1, 12, 0)
    with (
        mock.patch('main.datetime') as mock_datetime,
        mock.patch('builtins.open', mock.mock_open()) as mock_file
    ):
        mock_datetime.now.return_value = test_time
        main.save_last_checked_time()

        mock_file().write.assert_called_once_with(test_time.isoformat())


def test_check_feed_new_entries(mock_feedparser):
    """Test processing new feed entries"""
    # Create proper struct_time mock objects
    old_time = time.struct_time((2023, 1, 1, 10, 0, 0, 0, 0, 0))
    new_time = time.struct_time((2023, 1, 1, 12, 0, 0, 0, 0, 0))

    # Create mock entries with proper structure
    old_entry = mock.Mock(
        published_parsed=old_time,
        title="Old",
        description="Old issue",
        link="old"
    )
    new_entry = mock.Mock(
        published_parsed=new_time,
        title="New",
        description="New issue",
        link="new"
    )

    # Mock feedparser response
    mock_feedparser.parse.return_value.entries = [new_entry, old_entry]

    with (
        mock.patch(
            'main.get_last_checked_time',
            return_value=datetime(2023, 1, 1, 11, 0)
        ),
        mock.patch('main.send_pushover_notification') as mock_notify,
        mock.patch('main.save_last_checked_time') as mock_save
    ):
        main.check_feed()

        # Verify only new entry triggered notification
        mock_notify.assert_called_once_with(
            "New", "New issue", "new"
        )
        mock_save.assert_called_once()


def test_main_loop_execution(mock_time):
    """Test main loop execution flow"""
    with (
        mock.patch('main.check_feed') as mock_check,
        mock.patch('main.CHECK_INTERVAL', 0.1)  # Shorter interval for testing
    ):

        # Simulate keyboard interrupt after first iteration
        mock_time.sleep.side_effect = KeyboardInterrupt()
        main.main()

        mock_check.assert_called_once()
        mock_time.sleep.assert_called_once_with(0.1)
