import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])

regions = ["all", "América do Sul", "América do Norte", "América Central", "Europa", "Ásia", "Oriente Médio", "África", "Oceania", "Global"]
themes = ["all", "Geopolítica e Segurança", "Política Internacional", "Política Brasileira", "Economia Internacional", "Economia Brasileira", "Comércio e Finanças", "Meio Ambiente e Clima", "Ciência, Tecnologia e Inovação", "Direitos Humanos, Sociedade e Migrações", "Saúde", "Direito Internacional e Instituições", "Cultura, Mídia e Sociedade", "Outros / Multitemático"]
sources = ["all", "brazilian", "international"]

# Testa todas as combinações de filtros individuais para ver se alguma dá erro ou sempre 0
print("--- Testando Filtros Regionais ---")
for r in regions:
    filtered = [item for item in news if r == 'all' or item.get('region') == r]
    print(f"Região: {r:<20} | Resultados: {len(filtered)}")

print("\n--- Testando Filtros de Temas ---")
for t in themes:
    filtered = [item for item in news if t == 'all' or item.get('theme') == t]
    print(f"Tema: {t:<35} | Resultados: {len(filtered)}")

print("\n--- Testando Filtros de Origem ---")
for s in sources:
    if s == 'all':
        filtered = news
    elif s == 'brazilian':
        filtered = [item for item in news if item.get('is_brazilian') is True]
    else:
        filtered = [item for item in news if item.get('is_brazilian') is False]
    print(f"Origem: {s:<20} | Resultados: {len(filtered)}")
