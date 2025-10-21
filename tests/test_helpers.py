"""
Helper functions and classes for testing.
"""

from arrestx.model import WebRetrievalError


class MockWebRetrievalError(WebRetrievalError):
    """Mock WebRetrievalError for testing."""
    pass