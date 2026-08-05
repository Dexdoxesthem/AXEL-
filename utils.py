"""Shared helpers: logging and disk caching."""

import hashlib
import logging
from pathlib import Path

from config import CACHE_DIR


def setup_logging(level=logging.INFO):
    """Configure a single, consistent root logger for all AXEL apps."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    return logging.getLogger("axel")


def data_fingerprint(dataframe):
    """Stable sha256 fingerprint of a dataframe's schema + sample content.

    Used as a cache key so cached pipelines are invalidated whenever the
    underlying data changes.
    """
    hasher = hashlib.sha256()
    hasher.update("|".join(map(str, dataframe.columns)).encode("utf-8"))
    hasher.update(str(dataframe.shape).encode("utf-8"))
    sample = dataframe.head(100).to_json(orient="records")
    hasher.update(sample.encode("utf-8"))
    return hasher.hexdigest()[:16]


def cache_path(prefix, fingerprint):
    """Path to a cached artifact for ``prefix`` + ``fingerprint``."""
    Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
    return Path(CACHE_DIR) / f"{prefix}_{fingerprint}.joblib"
