import os
import string
import random
from flask import Flask, request, redirect, render_template_string
import psycopg
from psycopg.rows import tuple_row

app = Flask(__name__)

# Database connection parameters come from environment variables.
# This is standard practice: configuration lives outside the code.
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "shortener"),
    "user": os.environ.get("DB_USER", "shortener"),
    "password": os.environ.get("DB_PASSWORD", "123"),
}


def get_conn():
    """Open a new database connection."""
    return psycopg.connect(**DB_CONFIG)


def init_db():
    """Create the urls table if it doesn't exist yet."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                code TEXT PRIMARY KEY,
                long_url TEXT NOT NULL
            )
        """)


def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


FORM_HTML = """
<!doctype html>
<title>URL Shortener</title>
<h1>URL Shortener :)</h1>
<form method="post" action="/shorten">
    <input type="url" name="long_url" placeholder="https://example.com/very/long/url" required style="width:400px">
    <button type="submit">Shorten</button>
</form>
{% if short_url %}
    <p>Your short URL: <a href="{{ short_url }}">{{ short_url }}</a></p>
{% endif %}
"""


@app.route("/")
def home():
    return render_template_string(FORM_HTML)


@app.route("/shorten", methods=["POST"])
def shorten():
    long_url = request.form["long_url"]

    with get_conn() as conn:
        while True:
            code = generate_code()
            existing = conn.execute(
                "SELECT 1 FROM urls WHERE code = %s", (code,)
            ).fetchone()
            if not existing:
                break

        conn.execute(
            "INSERT INTO urls (code, long_url) VALUES (%s, %s)",
            (code, long_url),
        )

    short_url = request.host_url + code
    return render_template_string(FORM_HTML, short_url=short_url)


@app.route("/<code>")
def follow(code):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT long_url FROM urls WHERE code = %s", (code,)
        ).fetchone()

    if row:
        return redirect(row[0])
    return "Short URL not found", 404


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
