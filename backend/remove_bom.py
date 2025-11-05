import io, os
p = os.path.join(os.path.dirname(__file__), '..', 'Novo Front', 'templates', 'orders', 'confirm.html')
with open(p, 'rb') as f:
    data = f.read()
# decode permissively
text = data.decode('utf-8-sig')
with open(p, 'w', encoding='utf-8') as f:
    f.write(text)
print('rewrote', p)

