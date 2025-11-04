import sqlite3, os, json
DB = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
print('DB path ->', DB)
if not os.path.exists(DB):
    print('NO_DB')
else:
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print('TABLES:', tables)
    try:
        cur.execute('SELECT count(*) FROM django_migrations')
        c=cur.fetchone()[0]
        print('django_migrations count', c)
        cur.execute("SELECT app, name, id FROM django_migrations ORDER BY app, name LIMIT 50")
        rows=cur.fetchall()
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    except Exception as e:
        print('ERR', e)
    conn.close()

