# Farg‘ona tumani Maktabgacha va maktab ta’limi bo‘limi — portal MVP

Flask + SQLite asosidagi ikki tilli (o‘zbek/rus) rasmiy portal prototipi. Moslashuvchan dizayn, yangiliklar, hujjatlar, ta’lim tashkilotlari, statistika va administrator bo‘limi mavjud.

## Ishga tushirish

1. Python 3.10+ o‘rnating.
2. Terminalda loyiha papkasiga kiring.
3. `python -m venv .venv` va virtual muhitni faollashtiring.
4. `pip install -r requirements.txt`
5. Administrator parolini muhit o‘zgaruvchisi orqali belgilang:
   - Linux/macOS: `export ADMIN_USERNAME=admin` va `export ADMIN_PASSWORD='kuchli-parol'`
   - Windows PowerShell: `$env:ADMIN_USERNAME='admin'` va `$env:ADMIN_PASSWORD='kuchli-parol'`
6. `python app.py`
7. Sayt: `http://127.0.0.1:5000`; admin: `/admin/login`.

Agar `ADMIN_PASSWORD` berilmasa, dastlabki sinov uchun `ChangeMe-2026!` ishlatiladi. Internetga chiqarishdan oldin albatta o‘zgartiring. `SECRET_KEY` ham kuchli tasodifiy qiymatga almashtirilsin. Ishlab chiqarish muhitida `FLASK_DEBUG` yoqilmasin va HTTPS, zaxira nusxa, kirish huquqlari hamda server sozlamalari ta’minlansin.

## Muhim

- Bu ishga tayyor boshlang‘ich prototip; hozircha domen yoki hostingga joylashtirilmagan.
- Yangilik rasmlari hozir URL orqali ulanadi. Hujjatlar ham fayl havolasi orqali beriladi.
- Maktablar ro‘yxatini admin orqali qo‘shish mumkin; boshlang‘ich ma’lumotlar faqat tasdiqlanganidan keyin kiritilsin.
- Ko‘rsatilgan statistikalar namunaviy boshlang‘ich qiymatlar bo‘lib, e’lon qilishdan oldin rasmiy ma’lumot bilan tekshirilishi kerak.
