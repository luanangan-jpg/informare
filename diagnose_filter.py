import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])

print("--- Testando filtro 'international' ---")
# Simula a lógica do JS:
# source === 'international' -> matchSource = item.is_brazilian === false
filtered = [item for item in news if item.get('is_brazilian') is False]

print(f"Total de itens após o filtro 'international': {len(filtered)}")
print(f"{'Fonte':<25} | {'Origem (is_br)':<14} | {'Título'}")
print("-" * 100)
for item in filtered[:10]:
    source = item.get('source_name', 'N/A')
    is_br = str(item.get('is_brazilian', 'N/A'))
    title = item.get('title', 'N/A')[:50]
    print(f"{source:<25} | {is_br:<14} | {title}")
