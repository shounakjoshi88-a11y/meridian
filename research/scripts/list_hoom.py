import json
p = r'D:\Q_project\meridian\research\raw\master'
d = json.load(open(p, encoding='utf-8'))
for t in d['tree']:
    if t['type'] == 'blob' and ('HOOM' in t['path'] or 'Ontologies' in t['path']):
        print(repr(t['path']), t.get('size'), t['sha'])