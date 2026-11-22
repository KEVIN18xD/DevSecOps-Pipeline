"""
Deliberately Insecure FastAPI Application — DevSecOps Pipeline Lab
==================================================================
This application contains **intentional** security vulnerabilities for
educational purposes.  Each vulnerability is labeled with:
  • the CWE it represents, and
  • the pipeline stage expected to detect it (SAST / DAST / both / none).

⚠️  DO NOT deploy this application in any production or internet-facing
    environment.
"""

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlite3
import subprocess
import hashlib

# ── VULN-1  Hardcoded Credentials (CWE-798) ─── detected by: SAST ──────────
SECRET_KEY = "super-secret-key-12345"
DB_PASS = "admin123!"
API_KEY = "sk-prod-a1b2c3d4e5f6g7h8i9j0"

app = FastAPI(title="Vulnerable Demo App")

# ── Database setup (in-memory SQLite) ───────────────────────────────────────
def init_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)"
    )
    cur.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin')")
    cur.execute("INSERT INTO users VALUES (2, 'alice', 'password', 'user')")
    conn.commit()
    return conn

db = init_db()


# ── Route 1  Home page ─────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html><head><title>Vulnerable App</title></head><body>
    <h1>DevSecOps Vulnerable Demo</h1>
    <ul>
        <li><a href="/search?q=test">Search (XSS)</a></li>
        <li><a href="/login">Login (SQLi)</a></li>
        <li><a href="/admin">Admin Panel (Broken Access Control)</a></li>
        <li><a href="/ping?host=localhost">Ping (Command Injection)</a></li>
        <li><a href="/file?name=readme.txt">File Reader (Path Traversal)</a></li>
        <li><a href="/hash">Hash (Insecure Crypto)</a></li>
    </ul>
    </body></html>
    """


# ── VULN-2  Reflected XSS (CWE-79) ─── detected by: DAST ──────────────────
# Payload: /search?q=<script>alert(1)</script>
@app.get("/search", response_class=HTMLResponse)
async def search(q: str = ""):
    return f"""
    <html><head><title>Search</title></head><body>
    <h1>Search</h1>
    <form><input name="q" value="{q}"><button>Search</button></form>
    <h2>Results for: {q}</h2>
    <p>No results found.</p>
    </body></html>
    """


# ── VULN-3  SQL Injection (CWE-89) ─── detected by: SAST + DAST ───────────
# Payload: username = admin'--   password = anything
@app.get("/login", response_class=HTMLResponse)
async def login_form():
    return """
    <html><head><title>Login</title></head><body>
    <h1>Login</h1>
    <form method="post" action="/login">
        <label>Username: <input name="username"></label><br>
        <label>Password: <input name="password" type="password"></label><br>
        <button type="submit">Login</button>
    </form>
    </body></html>
    """

@app.post("/login", response_class=HTMLResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cur = db.cursor()
    cur.execute(query)
    user = cur.fetchone()
    if user:
        return f"<html><body><h1>Welcome, {username}!</h1><p>Role: {user[3]}</p></body></html>"
    return "<html><body><h1>Login failed</h1></body></html>"


# ── VULN-4  Broken Access Control (CWE-284) ─── detected by: NONE ──────────
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    cur = db.cursor()
    cur.execute("SELECT id, username, role FROM users")
    rows = cur.fetchall()
    table = "".join(f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>" for r in rows)
    return f"""
    <html><head><title>Admin</title></head><body>
    <h1>Admin Panel</h1>
    <table border="1">
        <tr><th>ID</th><th>Username</th><th>Role</th></tr>
        {table}
    </table>
    </body></html>
    """


# ── VULN-5  OS Command Injection (CWE-78) ─── detected by: SAST + DAST ────
# Payload: /ping?host=localhost;cat+/etc/passwd
@app.get("/ping", response_class=HTMLResponse)
async def ping(host: str = "localhost"):
    result = subprocess.run(
        f"ping -c 1 {host}",
        shell=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return f"""
    <html><head><title>Ping</title></head><body>
    <h1>Ping {host}</h1>
    <pre>{result.stdout}\n{result.stderr}</pre>
    </body></html>
    """


# ── VULN-6  Path Traversal (CWE-22) ─── detected by: SAST + DAST ──────────
# Payload: /file?name=../../etc/passwd
@app.get("/file", response_class=HTMLResponse)
async def read_file(name: str = "readme.txt"):
    try:
        with open(f"/app/files/{name}") as f:
            content = f.read()
    except Exception as e:
        content = str(e)
    return f"""
    <html><head><title>File</title></head><body>
    <h1>File: {name}</h1>
    <pre>{content}</pre>
    </body></html>
    """


# ── VULN-7  Insecure Cryptography — MD5 (CWE-327) ─── detected by: NONE ───
@app.get("/hash", response_class=HTMLResponse)
async def hash_form():
    return """
    <html><head><title>Hash</title></head><body>
    <h1>MD5 Hash Generator</h1>
    <form method="post" action="/hash">
        <label>Text: <input name="text"></label>
        <button type="submit">Hash</button>
    </form>
    </body></html>
    """

@app.post("/hash", response_class=HTMLResponse)
async def hash_text(text: str = Form(...)):
    md5 = hashlib.md5(text.encode()).hexdigest()
    return f"""
    <html><head><title>Hash Result</title></head><body>
    <h1>MD5 Result</h1>
    <p>Input: {text}</p>
    <p>MD5: {md5}</p>
    </body></html>
    """
