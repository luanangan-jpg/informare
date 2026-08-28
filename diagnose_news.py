import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])
print(f"Total news items: {len(news)}")
print(f"{'Fonte':<25} | {'Região':<16} | {'Origem (is_br)':<14} | {'Título'}")
print("-" * 100)
for item in news[:10]:
    source = item.get('source_name', 'N/A')
    region = item.get('region', 'N/A')
    is_br = str(item.get('is_brazilian', 'N/A'))
    title = item.get('title', 'N/A')[:50]
    print(f"{source:<25} | {region:<16} | {is_br:<14} | {title}")
