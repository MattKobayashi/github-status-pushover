#!/usr/bin/env python3
from unittest import mock

import pytest


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock required environment variables."""

    monkeypatch.setenv("PUSHOVER_TOKEN", "test_token")
    monkeypatch.setenv("PUSHOVER_USER", "test_user")
    monkeypatch.setenv("CHECK_INTERVAL", "300")

    # Keep timing stable for tests.
    monkeypatch.setenv("REQUEST_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("PUSHOVER_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("PUSHOVER_BACKOFF_BASE_SECONDS", "0.01")
    monkeypatch.setenv("PUSHOVER_BACKOFF_MAX_SECONDS", "0.01")


@pytest.fixture
def mock_time():
    """Mock for time module."""

    with mock.patch("main.time") as mocked:
        yield mocked


@pytest.fixture
def mock_feedparser():
    """Mock for feedparser module."""

    with mock.patch("main.feedparser") as mocked:
        yield mocked
