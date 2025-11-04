import sqlite3, json, os
DB = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
out = os.path.join(os.path.dirname(__file__), 'tmp_methods.json')
res = {'db': DB, 'methods': []}
if os.path.exists(DB):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    try:
        cur.execute('SELECT uuid, code, name, type, fee_percent, fee_fixed FROM payment_paymentmethod')
        rows = cur.fetchall()
        for r in rows:
            res['methods'].append({'uuid': r[0], 'code': r[1], 'name': r[2], 'type': r[3], 'fee_percent': str(r[4]), 'fee_fixed': str(r[5])})
    except Exception as e:
        res['error'] = str(e)
    conn.close()
else:
    res['error'] = 'db not found'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=2)
print('WROTE', out)

