import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])
for item in news:
    if "nepal" in item.get('title', '').lower():
        print(json.dumps(item, indent=2, ensure_ascii=False))
