"""Tests for the URL shortener app."""
import pytest
from app import create_app, get_conn


@pytest.fixture
def client():
    """Provide a Flask test client with a clean database."""
    app = create_app()
    app.config["TESTING"] = True

    # Clear the urls table before each test so tests don't interfere
    with get_conn() as conn:
        conn.execute("DELETE FROM urls")

    with app.test_client() as client:
        yield client


def test_home_page_loads(client):
    """The home page returns a 200 and contains the form."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"URL Shortener" in response.data
    assert b"<form" in response.data


def test_shorten_creates_short_url(client):
    """Submitting a URL produces a short code and stores it."""
    response = client.post("/shorten", data={"long_url": "https://example.com"})
    assert response.status_code == 200
    assert b"Your short URL:" in response.data

    # Verify it's actually in the database
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM urls").fetchone()
        assert row[0] == 1


def test_follow_redirects_to_long_url(client):
    """Visiting a short code redirects to the original URL."""
    # First, create a short URL
    client.post("/shorten", data={"long_url": "https://example.com/hello"})

    # Get the code that was just stored
    with get_conn() as conn:
        row = conn.execute("SELECT code FROM urls").fetchone()
        code = row[0]

    # Now visit it
    response = client.get(f"/{code}")
    assert response.status_code == 302  # redirect
    assert response.headers["Location"] == "https://example.com/hello"


def test_unknown_code_returns_404(client):
    """Visiting a non-existent code returns 404."""
    response = client.get("/nopenope")
    assert response.status_code == 404
