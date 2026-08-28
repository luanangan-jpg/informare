import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])
print("Notícias classificadas como América do Sul:")
print("-" * 120)
for item in news:
    if item.get('region') == "América do Sul":
        print(f"Fonte: {item.get('source_name'):<20} | Título: {item.get('title')[:80]}")
