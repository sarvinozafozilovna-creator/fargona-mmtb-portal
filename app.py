import os, sqlite3
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE, 'portal.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-before-deployment')


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS news(id INTEGER PRIMARY KEY, title_uz TEXT NOT NULL, title_ru TEXT NOT NULL DEFAULT '', body_uz TEXT NOT NULL, body_ru TEXT NOT NULL DEFAULT '', image_url TEXT DEFAULT '', published INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY, title_uz TEXT NOT NULL, title_ru TEXT NOT NULL DEFAULT '', category TEXT DEFAULT 'Hujjat', file_url TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS schools(id INTEGER PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'Maktab', address TEXT DEFAULT '', phone TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS stats(id INTEGER PRIMARY KEY, label_uz TEXT NOT NULL, label_ru TEXT NOT NULL DEFAULT '', value TEXT NOT NULL, sort_order INTEGER DEFAULT 0);
        ''')
        if not c.execute('SELECT id FROM users LIMIT 1').fetchone():
            username = os.environ.get('ADMIN_USERNAME', 'admin')
            password = os.environ.get('ADMIN_PASSWORD', 'ChangeMe-2026!')
            c.execute('INSERT INTO users(username,password_hash) VALUES(?,?)', (username, generate_password_hash(password)))
        if not c.execute('SELECT id FROM stats LIMIT 1').fetchone():
            c.executemany('INSERT INTO stats(label_uz,label_ru,value,sort_order) VALUES(?,?,?,?)', [
                ('Umumta’lim maktablari','Общеобразовательные школы','64',1),
                ('Davlat maktabgacha ta’lim tashkilotlari','Государственные дошкольные организации','58',2),
                ('1-sinfga qabul qilingan o‘quvchilar','Учащиеся, принятые в 1-й класс','4 427',3),
            ])
        if not c.execute('SELECT id FROM news LIMIT 1').fetchone():
            c.execute('INSERT INTO news(title_uz,title_ru,body_uz,body_ru,image_url,published,created_at) VALUES(?,?,?,?,?,?,?)', (
                'Farg‘ona tumani ta’lim tizimiga xush kelibsiz','Добро пожаловать на портал образования Ферганского района',
                'Farg‘ona tumani Maktabgacha va maktab ta’limi bo‘limining rasmiy axborot portaliga xush kelibsiz. Yangiliklar, hujjatlar va ta’lim tashkilotlari haqidagi ma’lumotlar shu yerda joylashtiriladi.',
                'Добро пожаловать на официальный информационный портал отдела дошкольного и школьного образования Ферганского района. Здесь публикуются новости, документы и сведения об образовательных организациях.',
                '',1,datetime.now().strftime('%Y-%m-%d')))

init_db()


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('login', next=request.path))
        return fn(*args, **kwargs)
    return wrapped

@app.context_processor
def common():
    return {'lang': session.get('lang', 'uz')}

@app.get('/lang/<language>')
def set_language(language):
    if language in ('uz','ru'): session['lang'] = language
    return redirect(request.referrer or url_for('home'))

@app.get('/')
def home():
    language = session.get('lang','uz')
    with db() as c:
        news = c.execute('SELECT * FROM news WHERE published=1 ORDER BY id DESC LIMIT 6').fetchall()
        stats = c.execute('SELECT * FROM stats ORDER BY sort_order,id').fetchall()
        docs = c.execute('SELECT * FROM documents ORDER BY id DESC LIMIT 4').fetchall()
    return render_template('home.html', news=news, stats=stats, docs=docs, language=language)

@app.get('/news')
def news_list():
    with db() as c: items = c.execute('SELECT * FROM news WHERE published=1 ORDER BY id DESC').fetchall()
    return render_template('news.html', items=items, language=session.get('lang','uz'))

@app.get('/news/<int:item_id>')
def news_detail(item_id):
    with db() as c: item = c.execute('SELECT * FROM news WHERE id=? AND published=1',(item_id,)).fetchone()
    if not item: abort(404)
    return render_template('news_detail.html', item=item, language=session.get('lang','uz'))

@app.get('/documents')
def documents():
    with db() as c: items = c.execute('SELECT * FROM documents ORDER BY id DESC').fetchall()
    return render_template('documents.html', items=items, language=session.get('lang','uz'))

@app.get('/schools')
def schools():
    q = request.args.get('q','').strip()
    with db() as c:
        if q: items = c.execute('SELECT * FROM schools WHERE name LIKE ? OR kind LIKE ? ORDER BY name', (f'%{q}%',f'%{q}%')).fetchall()
        else: items = c.execute('SELECT * FROM schools ORDER BY name').fetchall()
    return render_template('schools.html', items=items, q=q, language=session.get('lang','uz'))

@app.get('/about')
def about(): return render_template('about.html', language=session.get('lang','uz'))

@app.get('/contact')
def contact(): return render_template('contact.html', language=session.get('lang','uz'))

@app.route('/admin/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username, password = request.form.get('username',''), request.form.get('password','')
        with db() as c: user = c.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session['admin_id'] = user['id']
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        flash('Login yoki parol noto‘g‘ri. / Неверный логин или пароль.', 'error')
    return render_template('login.html')

@app.get('/admin/logout')
def logout(): session.clear(); return redirect(url_for('home'))

@app.get('/admin')
@admin_required
def admin_dashboard():
    with db() as c:
        counts = {t: c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('news','documents','schools','stats')}
        items = c.execute('SELECT * FROM news ORDER BY id DESC LIMIT 8').fetchall()
    return render_template('admin.html', counts=counts, items=items)

@app.route('/admin/news/new', methods=['GET','POST'])
@app.route('/admin/news/<int:item_id>/edit', methods=['GET','POST'])
@admin_required
def admin_news_form(item_id=None):
    with db() as c: item = c.execute('SELECT * FROM news WHERE id=?',(item_id,)).fetchone() if item_id else None
    if request.method == 'POST':
        vals = (request.form.get('title_uz','').strip(), request.form.get('title_ru','').strip(), request.form.get('body_uz','').strip(), request.form.get('body_ru','').strip(), request.form.get('image_url','').strip(), 1 if request.form.get('published') else 0)
        if not vals[0] or not vals[2]: flash('O‘zbekcha sarlavha va matn majburiy.', 'error')
        else:
            with db() as c:
                if item_id: c.execute('UPDATE news SET title_uz=?,title_ru=?,body_uz=?,body_ru=?,image_url=?,published=? WHERE id=?', (*vals,item_id))
                else: c.execute('INSERT INTO news(title_uz,title_ru,body_uz,body_ru,image_url,published,created_at) VALUES(?,?,?,?,?,?,?)', (*vals,datetime.now().strftime('%Y-%m-%d')))
            flash('Yangilik saqlandi.', 'success'); return redirect(url_for('admin_dashboard'))
    return render_template('news_form.html', item=item)

@app.post('/admin/news/<int:item_id>/delete')
@admin_required
def admin_news_delete(item_id):
    with db() as c: c.execute('DELETE FROM news WHERE id=?',(item_id,))
    flash('Yangilik o‘chirildi.', 'success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/documents/new', methods=['GET','POST'])
@admin_required
def admin_document_new():
    if request.method == 'POST':
        title_uz=request.form.get('title_uz','').strip(); file_url=request.form.get('file_url','').strip()
        if not title_uz or not file_url: flash('Sarlavha va fayl havolasi kerak.', 'error')
        else:
            with db() as c: c.execute('INSERT INTO documents(title_uz,title_ru,category,file_url,created_at) VALUES(?,?,?,?,?)',(title_uz,request.form.get('title_ru','').strip(),request.form.get('category','Hujjat'),file_url,datetime.now().strftime('%Y-%m-%d')))
            flash('Hujjat qo‘shildi.', 'success'); return redirect(url_for('documents'))
    return render_template('document_form.html')

@app.route('/admin/schools/new', methods=['GET','POST'])
@admin_required
def admin_school_new():
    if request.method == 'POST':
        name=request.form.get('name','').strip()
        if not name: flash('Tashkilot nomini kiriting.', 'error')
        else:
            with db() as c: c.execute('INSERT INTO schools(name,kind,address,phone) VALUES(?,?,?,?)',(name,request.form.get('kind','Maktab'),request.form.get('address',''),request.form.get('phone','')))
            flash('Ta’lim tashkiloti qo‘shildi.', 'success'); return redirect(url_for('schools'))
    return render_template('school_form.html')

@app.route('/admin/stats', methods=['GET','POST'])
@admin_required
def admin_stats():
    with db() as c:
        if request.method == 'POST':
            for row in c.execute('SELECT id FROM stats').fetchall():
                c.execute('UPDATE stats SET value=? WHERE id=?',(request.form.get(f'value_{row["id"]}','').strip(),row['id']))
            flash('Statistika saqlandi.', 'success'); return redirect(url_for('admin_stats'))
        items=c.execute('SELECT * FROM stats ORDER BY sort_order,id').fetchall()
    return render_template('stats_form.html', items=items)

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', host='0.0.0.0', port=int(os.environ.get('PORT','5000')))
