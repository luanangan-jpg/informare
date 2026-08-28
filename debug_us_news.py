import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])
print("Notícias com palavras-chave de EUA/Trump/Estados Unidos:")
for item in news:
    title = item.get('title', '')
    summary = item.get('summary', '')
    combined = (title + " " + summary).lower()
    if any(k in combined for k in ["eua", "estados unidos", "trump", "biden"]):
        print(f"Fonte: {item.get('source_name'):<20} | Região: {item.get('region'):<15} | Título: {title[:70]}")
