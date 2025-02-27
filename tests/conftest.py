#!/usr/bin/env python3
from unittest import mock
import pytest


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock required environment variables"""
    monkeypatch.setenv('PUSHOVER_TOKEN', 'test_token')
    monkeypatch.setenv('PUSHOVER_USER', 'test_user')
    monkeypatch.setenv('CHECK_INTERVAL', '300')


@pytest.fixture
def mock_requests():
    """Mock for requests module"""
    with mock.patch('main.requests') as mock_requests:
        yield mock_requests


@pytest.fixture
def mock_time():
    """Mock for time module"""
    with mock.patch('main.time') as mock_time:
        yield mock_time


@pytest.fixture
def mock_feedparser():
    """Mock for feedparser module"""
    with mock.patch('main.feedparser') as mock_feedparser:
        yield mock_feedparser
