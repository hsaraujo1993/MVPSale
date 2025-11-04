import sqlite3, os, json

DB = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
if not os.path.exists(DB):
    print('NO_DB', DB)
else:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT app, name, id FROM django_migrations WHERE app='payment' ORDER BY name")
    rows = cur.fetchall()
    if not rows:
        print('NO_MIGRATIONS_FOUND')
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    conn.close()
