import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])
sources_status = {}
for item in news:
    name = item.get('source_name')
    is_br = item.get('is_brazilian')
    if name not in sources_status:
        sources_status[name] = set()
    sources_status[name].add(is_br)

for name, statuses in sources_status.items():
    print(f"Fonte: {name:<30} | is_brazilian detectados: {statuses}")
