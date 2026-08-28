import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])

print("="*130)
print("TABELA DE VALIDAÇÃO FINAL (Filtros de Região e Origem independentes)")
print("="*130)
print(f"{'Fonte':<28} | {'Origem Fonte':<16} | {'Região Classificada':<22} | {'Título'}")
print("-" * 140)

# 1. Fontes Brasileiras falando sobre assuntos internacionais (ex: EUA, Europa)
br_int_news = [item for item in news if item.get('is_brazilian') is True and item.get('region') != "América do Sul"]

# 2. Fontes Internacionais falando sobre assuntos internacionais
int_int_news = [item for item in news if item.get('is_brazilian') is False and item.get('region') != "América do Sul"]

# 3. Notícias sobre a América do Sul (de qualquer fonte)
s_america_news = [item for item in news if item.get('region') == "América do Sul"]

# Pega amostras de cada grupo para a tabela
sample = []
sample.extend(br_int_news[:4])
sample.extend(int_int_news[:3])
sample.extend(s_america_news[:3])

for item in sample[:10]:
    source = item.get('source_name', 'N/A')
    origem = "Brasileira" if item.get('is_brazilian') else "Internacional"
    regiao = item.get('region', 'N/A')
    title = item.get('title', 'N/A')[:65]
    print(f"{source:<28} | {origem:<16} | {regiao:<22} | {title}")

print("="*130)
print(f"\nEstatísticas de Coleta Final:")
print(f"  - Total de notícias de fontes Brasileiras cobrindo regiões Estrangeiras: {len(br_int_news)}")
print(f"  - Total de notícias de fontes Internacionais cobrindo regiões Estrangeiras: {len(int_int_news)}")
print(f"  - Total de notícias gerais mapeadas para a América do Sul: {len(s_america_news)}")
