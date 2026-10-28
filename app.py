import os, sqlite3
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, abort

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE, "portal.db"))
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-production")

def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS news(id INTEGER PRIMARY KEY, title_uz TEXT NOT NULL, title_ru TEXT DEFAULT '', body_uz TEXT NOT NULL, body_ru TEXT DEFAULT '', image_url TEXT DEFAULT '', published INTEGER DEFAULT 1, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY, title_uz TEXT NOT NULL, title_ru TEXT DEFAULT '', category TEXT DEFAULT 'Hujjat', file_url TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schools(id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT DEFAULT 'Maktab', address TEXT DEFAULT '', phone TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS stats(id INTEGER PRIMARY KEY, label_uz TEXT NOT NULL, label_ru TEXT DEFAULT '', value TEXT NOT NULL, sort_order INTEGER DEFAULT 0);
        """)
        if c.execute("SELECT COUNT(*) FROM stats").fetchone()[0] == 0:
            c.executemany("INSERT INTO stats(label_uz,label_ru,value,sort_order) VALUES(?,?,?,?)", [
                ("Umumta’lim maktablari","Общеобразовательные школы","64",1),
                ("Davlat maktabgacha ta’lim tashkilotlari","Государственные дошкольные организации","58",2),
                ("1-sinfga qabul qilingan o‘quvchilar","Учащиеся, принятые в 1-й класс","4 427",3)])
        if c.execute("SELECT COUNT(*) FROM news").fetchone()[0] == 0:
            c.execute("INSERT INTO news(title_uz,title_ru,body_uz,body_ru,created_at) VALUES(?,?,?,?,?)", (
                "Farg‘ona tumani ta’lim axborot portaliga xush kelibsiz",
                "Добро пожаловать на образовательный портал Ферганского района",
                "Ushbu portalda ta’lim tizimidagi yangiliklar, rasmiy hujjatlar va statistik ma’lumotlar bilan tanishishingiz mumkin.",
                "На портале представлены новости, документы и статистические данные системы образования.",
                datetime.now().strftime("%Y-%m-%d")))
init_db()

def lang(): return session.get("lang", "uz")

@app.get("/lang/<language>")
def set_language(language):
    if language in ("uz","ru"): session["lang"] = language
    return redirect(request.referrer or url_for("home"))

@app.get("/")
def home():
    with db() as c:
        news = c.execute("SELECT * FROM news WHERE published=1 ORDER BY id DESC LIMIT 6").fetchall()
        stats = c.execute("SELECT * FROM stats ORDER BY sort_order,id").fetchall()
        docs = c.execute("SELECT * FROM documents ORDER BY id DESC LIMIT 4").fetchall()
    return render_template("home.html", news=news, stats=stats, docs=docs, lang=lang())

@app.get("/news")
def news_list():
    with db() as c: items = c.execute("SELECT * FROM news WHERE published=1 ORDER BY id DESC").fetchall()
    return render_template("news.html", items=items, lang=lang())

@app.get("/news/<int:item_id>")
def news_detail(item_id):
    with db() as c: item = c.execute("SELECT * FROM news WHERE id=? AND published=1",(item_id,)).fetchone()
    if item is None: abort(404)
    return render_template("news_detail.html", item=item, lang=lang())

@app.get("/documents")
def documents():
    with db() as c: items = c.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
    return render_template("documents.html", items=items, lang=lang())

@app.get("/schools")
def schools():
    q = request.args.get("q","").strip()
    with db() as c:
        if q:
            items = c.execute("SELECT * FROM schools WHERE name LIKE ? OR kind LIKE ? OR address LIKE ? ORDER BY name",(f"%{q}%",f"%{q}%",f"%{q}%")).fetchall()
        else: items = c.execute("SELECT * FROM schools ORDER BY name").fetchall()
    return render_template("schools.html", items=items, q=q, lang=lang())

@app.get("/statistics")
def statistics():
    with db() as c: stats = c.execute("SELECT * FROM stats ORDER BY sort_order,id").fetchall()
    return render_template("statistics.html", stats=stats, lang=lang())

@app.get("/digitization")
def digitization(): return render_template("digitization.html", lang=lang())

@app.get("/about")
def about(): return render_template("about.html", lang=lang())

@app.get("/contact")
def contact(): return render_template("contact.html", lang=lang())

@app.errorhandler(404)
def not_found(e): return render_template("404.html", lang=lang()), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","5000")))
