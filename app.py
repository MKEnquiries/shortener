from flask import Flask, request, redirect, render_template_string
import sqlite3
import string
import random

app = Flask(__name__)
DB_PATH = "shortener.db"


def init_db():
    """Create the urls table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            code TEXT PRIMARY KEY,
            long_url TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def generate_code(length=6):
    """Generate a random short code like 'a3Bx9Z'."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


# Simple inline HTML — we'll move this to a proper template later
FORM_HTML = """
<!doctype html>
<title>URL Shortener</title>
<h1>URL Shortener</h1>
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

    # Generate a unique code (retry if collision)
    conn = sqlite3.connect(DB_PATH)
    while True:
        code = generate_code()
        existing = conn.execute("SELECT 1 FROM urls WHERE code = ?", (code,)).fetchone()
        if not existing:
            break

    conn.execute("INSERT INTO urls (code, long_url) VALUES (?, ?)", (code, long_url))
    conn.commit()
    conn.close()

    short_url = request.host_url + code
    return render_template_string(FORM_HTML, short_url=short_url)


@app.route("/<code>")
def follow(code):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT long_url FROM urls WHERE code = ?", (code,)).fetchone()
    conn.close()

    if row:
        return redirect(row[0])
    return "Short URL not found", 404


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
