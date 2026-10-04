import json
p = r'D:\Q_project\meridian\research\raw\master'
d = json.load(open(p, encoding='utf-8'))
print('truncated:', d.get('truncated'), 'entries:', len(d['tree']))
blobs = [t for t in d['tree'] if t['type'] == 'blob']
print('blobs:', len(blobs), ' total bytes:', sum(t.get('size', 0) for t in blobs))
print()
for t in blobs:
    print(f"{t.get('size', 0):>10}  {t['path']}")