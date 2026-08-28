import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])

# Agrupa as notícias pelos tipos pedidos
br_source_int_content = []  # Fonte BR, Assunto Internacional
int_source_br_content = []  # Fonte Int, Assunto Brasil
br_source_br_content = []   # Fonte BR, Assunto Brasil
others = []

for item in news:
    is_br_source = item.get('is_brazilian')
    content_tag = item.get('content_tag')
    
    if is_br_source and content_tag == "Internacional":
        br_source_int_content.append(item)
    elif not is_br_source and content_tag == "Brasil":
        int_source_br_content.append(item)
    elif is_br_source and content_tag == "Brasil":
        br_source_br_content.append(item)
    else:
        others.append(item)

# Seleciona os itens para a amostra final de 10 itens
sample_items = []
# Pega 3 de BR Source / Int Content
sample_items.extend(br_source_int_content[:3])
# Pega todas de Int Source / BR Content
sample_items.extend(int_source_br_content[:2])
# Pega 3 de BR Source / BR Content
sample_items.extend(br_source_br_content[:3])

# Completa até 10 com as outras
needed = 10 - len(sample_items)
if needed > 0:
    sample_items.extend(others[:needed])

print("="*130)
print(f"TABELA DE VALIDAÇÃO: 10 NOTÍCIAS REAIS")
print("="*130)
print(f"{'Fonte':<28} | {'Origem Fonte (Atrib 2)':<22} | {'Região (Atrib 1)':<18} | {'Tag Conteúdo (Atrib 3)':<22} | {'Título'}")
print("-" * 140)
for item in sample_items[:10]:
    source = item.get('source_name', 'N/A')
    origem = "Brasileira" if item.get('is_brazilian') else "Internacional"
    regiao = item.get('region', 'N/A')
    tag = item.get('content_tag', 'N/A')
    title = item.get('title', 'N/A')[:55]
    print(f"{source:<28} | {origem:<22} | {regiao:<18} | {tag:<22} | {title}")
print("="*130)

print(f"\nEstatísticas de Coleta:")
print(f"  - Total de notícias de Fonte BR sobre assuntos Internacionais: {len(br_source_int_content)}")
print(f"  - Total de notícias de Fonte Int sobre assuntos do Brasil: {len(int_source_br_content)}")
print(f"  - Total de notícias de Fonte BR sobre assuntos do Brasil: {len(br_source_br_content)}")
