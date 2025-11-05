import os
p = os.path.join(os.path.dirname(__file__), '..', 'Novo Front', 'templates', 'orders', 'confirm.html')
with open(p, 'rb') as f:
    data = f.read(4)
print('path:', p)
print('first bytes:', data)
print('starts with UTF-8 BOM:', data.startswith(b'\xef\xbb\xbf'))

