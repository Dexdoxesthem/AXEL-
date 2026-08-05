"""Tests for config.py settings."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


def test_risk_thresholds_present_and_sane():
    assert 0 < config.RISK_GPA_THRESHOLD <= 10
    assert 0 < config.RISK_ATTENDANCE_THRESHOLD <= 100
    assert 0 < config.GPA_LOW_THRESHOLD <= 100


def test_modelling_settings():
    assert config.CV_FOLDS >= 2
    assert 0 <= config.KMEANS_MIN_K < config.KMEANS_MAX_K
    assert isinstance(config.RANDOM_STATE, int)


def test_cache_dir_is_absolute_path():
    assert os.path.isabs(config.CACHE_DIR)
    assert config.CACHE_DB.endswith("axel.db")


def test_app_settings():
    assert isinstance(config.FLASK_PORT, int)
    assert isinstance(config.DASH_PORT, int)
    assert isinstance(config.STREAMLIT_PORT, int)
    assert config.DEFAULT_HOST


def test_auth_password_configured():
    assert config.AUTH_PASSWORD
