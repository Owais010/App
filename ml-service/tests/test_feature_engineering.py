"""
Tests for Feature Engineering module.
"""

import numpy as np
import pytest

from app.feature_engineering import (
    FEATURE_NAMES,
    FeatureVector,
    _empty_features,
    feature_vector_to_array,
    invalidate_cache,
)


class TestFeatureVector:
    """Test FeatureVector schema and conversions."""

    def test_empty_features_returns_valid_vector(self):
        fv = _empty_features()
        assert fv.total_attempts == 0
        assert fv.accuracy == 0.0
        assert fv.days_since_last == -1.0  # sentinel

    def test_feature_vector_to_array_length(self, beginner_features):
        arr = feature_vector_to_array(beginner_features)
        assert len(arr) == 14
        assert arr.dtype == np.float64

    def test_feature_vector_to_array_order(self, intermediate_features):
        arr = feature_vector_to_array(intermediate_features)
        # Verify canonical order matches FEATURE_NAMES
        for i, name in enumerate(FEATURE_NAMES):
            assert arr[i] == getattr(intermediate_features, name), f"Mismatch at {name}"

    def test_feature_names_count(self):
        assert len(FEATURE_NAMES) == 14

    def test_validation_clamps_accuracy(self):
        """Accuracy must be [0, 1]."""
        fv = FeatureVector(accuracy=0.5)
        assert 0 <= fv.accuracy <= 1

    def test_validation_rejects_negative_attempts(self):
        """total_attempts must be >= 0."""
        with pytest.raises(Exception):
            FeatureVector(total_attempts=-1)


class TestFeatureCache:
    """Test in-memory cache operations."""

    def test_invalidate_specific_topic(self):
        from app.feature_engineering import _cache

        _cache[("u1", "t1")] = (0, _empty_features())
        _cache[("u1", "t2")] = (0, _empty_features())
        invalidate_cache("u1", "t1")
        assert ("u1", "t1") not in _cache
        assert ("u1", "t2") in _cache
        # Cleanup
        _cache.clear()

    def test_invalidate_all_topics_for_user(self):
        from app.feature_engineering import _cache

        _cache[("u1", "t1")] = (0, _empty_features())
        _cache[("u1", "t2")] = (0, _empty_features())
        _cache[("u2", "t1")] = (0, _empty_features())
        invalidate_cache("u1")
        assert ("u1", "t1") not in _cache
        assert ("u1", "t2") not in _cache
        assert ("u2", "t1") in _cache
        _cache.clear()
