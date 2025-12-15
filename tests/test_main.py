#!/usr/bin/env python3
from datetime import datetime, timezone
import time
from unittest import mock

import pytest
import requests

import main


def test_send_pushover_notification_success():
    session = mock.Mock()
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    session.post.return_value = resp

    main.send_pushover_notification(
        session=session,
        token="test_token",
        user="test_user",
        title="Test",
        message="Message",
        url="http://example.com",
    )

    session.post.assert_called_once_with(
        main.PUSHOVER_ENDPOINT,
        data={
            "token": "test_token",
            "user": "test_user",
            "message": "Message",
            "title": "Test",
            "url": "http://example.com",
        },
        timeout=main.get_request_timeout_seconds(),
    )


def test_send_pushover_notification_retries_on_timeout():
    session = mock.Mock()

    resp = mock.Mock()
    resp.raise_for_status.return_value = None

    session.post.side_effect = [
        requests.exceptions.Timeout("timeout1"),
        requests.exceptions.Timeout("timeout2"),
        resp,
    ]

    with mock.patch("main.time.sleep") as mock_sleep:
        main.send_pushover_notification(
            session=session,
            token="test_token",
            user="test_user",
            title="Test",
            message="Message",
            url="http://example.com",
        )

        assert session.post.call_count == 3
        assert mock_sleep.call_count == 2


def test_send_pushover_notification_nonretryable_400():
    session = mock.Mock()

    resp = mock.Mock(status_code=400, text="bad request")
    http_err = requests.HTTPError("400 Client Error", response=resp)
    resp.raise_for_status.side_effect = http_err

    session.post.return_value = resp

    with mock.patch("main.time.sleep") as mock_sleep:
        with pytest.raises(requests.HTTPError):
            main.send_pushover_notification(
                session=session,
                token="test_token",
                user="test_user",
                title="Test",
                message="Message",
                url="http://example.com",
            )

        session.post.assert_called_once()
        mock_sleep.assert_not_called()


def test_get_last_checked_time_file_exists(tmp_path):
    test_time = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    p = tmp_path / "last_checked"
    p.write_text(test_time.isoformat(), encoding="utf-8")

    result = main.get_last_checked_time(p)
    assert result == test_time


def test_get_last_checked_time_file_missing(tmp_path):
    fixed_now = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    missing = tmp_path / "does_not_exist"

    with mock.patch("main.utc_now", return_value=fixed_now):
        result = main.get_last_checked_time(missing)

    assert result == fixed_now


def test_get_last_checked_time_corrupt_file(tmp_path):
    fixed_now = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
    p = tmp_path / "last_checked"
    p.write_text("not-a-date", encoding="utf-8")

    with mock.patch("main.utc_now", return_value=fixed_now):
        result = main.get_last_checked_time(p)

    assert result == fixed_now


def test_save_last_checked_time_calls_atomic_write(tmp_path):
    p = tmp_path / "last_checked"
    naive_time = datetime(2023, 1, 1, 12, 0)

    with mock.patch("main.atomic_write_text") as mock_atomic:
        main.save_last_checked_time(p, naive_time)

    mock_atomic.assert_called_once()
    args, _kwargs = mock_atomic.call_args
    assert args[0] == p
    assert args[1].endswith("+00:00")


def test_check_feed_new_entries(tmp_path, mock_feedparser):
    old_time = time.struct_time((2023, 1, 1, 10, 0, 0, 0, 0, 0))
    new_time = time.struct_time((2023, 1, 1, 12, 0, 0, 0, 0, 0))

    old_entry = mock.Mock(
        published_parsed=old_time, title="Old", description="Old issue", link="old"
    )
    new_entry = mock.Mock(
        published_parsed=new_time, title="New", description="New issue", link="new"
    )

    mock_feedparser.parse.return_value.entries = [new_entry, old_entry]
    mock_feedparser.parse.return_value.bozo = False

    last_check_path = tmp_path / "last_checked"
    last_check_path.write_text(
        datetime(2023, 1, 1, 11, 0, tzinfo=timezone.utc).isoformat(),
        encoding="utf-8",
    )

    session = mock.Mock()

    with (
        mock.patch("main.send_pushover_notification") as mock_notify,
        mock.patch("main.save_last_checked_time") as mock_save,
    ):
        main.check_feed(
            session=session,
            token="test_token",
            user="test_user",
            rss_url="http://example.test/rss",
            last_check_path=last_check_path,
        )

        mock_notify.assert_called_once_with(
            session=session,
            token="test_token",
            user="test_user",
            title="New",
            message="New issue",
            url="new",
        )

        # Should persist the newest timestamp seen.
        expected_newest = datetime(2023, 1, 1, 12, 0, tzinfo=timezone.utc)
        mock_save.assert_called_once_with(last_check_path, expected_newest)


def test_check_feed_first_run_initializes_without_sending(tmp_path, mock_feedparser):
    entry_time = time.struct_time((2023, 1, 1, 12, 0, 0, 0, 0, 0))
    entry = mock.Mock(
        published_parsed=entry_time,
        title="New",
        description="New issue",
        link="new",
    )

    mock_feedparser.parse.return_value.entries = [entry]
    mock_feedparser.parse.return_value.bozo = False

    last_check_path = tmp_path / "last_checked"  # intentionally does not exist
    session = mock.Mock()

    with (
        mock.patch("main.send_pushover_notification") as mock_notify,
        mock.patch("main.save_last_checked_time") as mock_save,
    ):
        main.check_feed(
            session=session,
            token="test_token",
            user="test_user",
            rss_url="http://example.test/rss",
            last_check_path=last_check_path,
        )

        mock_notify.assert_not_called()
        mock_save.assert_called_once()


def test_main_loop_execution():
    mock_session = mock.Mock()

    with (
        mock.patch("main.check_feed") as mock_check,
        mock.patch("main.get_check_interval_seconds", return_value=0.1),
        mock.patch("main.requests.Session", return_value=mock_session),
        mock.patch("main.time.sleep", side_effect=SystemExit(0)) as mock_sleep,
    ):
        with pytest.raises(SystemExit) as excinfo:
            main.main()
        assert excinfo.value.code == 0

        mock_check.assert_called_once_with(
            session=mock_session,
            token="test_token",
            user="test_user",
        )
        mock_sleep.assert_called_once_with(0.1)


def test_html_to_text():
    html_input = "<p>Hello, <strong>world</strong>! & &copy;</p>"
    expected_output = "Hello, world! & ©"
    assert main.html_to_text(html_input) == expected_output


def test_html_to_text_with_p():
    html_input = "<p>First paragraph.</p><p>Second paragraph.</p>"
    expected_output = "First paragraph.\n\nSecond paragraph."
    assert main.html_to_text(html_input) == expected_output


def test_html_to_text_with_br():
    html_input = "First line<br />Second line<br/>Third line"
    expected_output = "First line\nSecond line\nThird line"
    assert main.html_to_text(html_input) == expected_output
