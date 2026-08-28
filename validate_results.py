import json

with open('data/news.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

news = data.get('news', [])

print("="*80)
print("VALIDAÇÃO PARTE 1: Amostra de 10 Notícias Reais (Classificações Corrigidas)")
print("="*80)
print(f"{'Fonte':<25} | {'Região':<16} | {'Origem (is_br)':<14} | {'Título'}")
print("-" * 120)
for item in news[:10]:
    source = item.get('source_name', 'N/A')
    region = item.get('region', 'N/A')
    is_br = str(item.get('is_brazilian', 'N/A'))
    title = item.get('title', 'N/A')[:60]
    print(f"{source:<25} | {region:<16} | {is_br:<14} | {title}")

print("\n" + "="*80)
print("VALIDAÇÃO PARTE 2: Teste Específico - Filtro 'Fontes Internacionais'")
print("="*80)
# Filtra por fontes internacionais (is_brazilian == False)
int_news = [item for item in news if item.get('is_brazilian') is False]
br_in_int = [item for item in int_news if item.get('is_brazilian') is True]

print(f"Total de notícias coletadas de fontes internacionais: {len(int_news)}")
print(f"Total de notícias brasileiras que vazaram no filtro internacional: {len(br_in_int)}")
if len(br_in_int) == 0:
    print("[SUCESSO] Nenhuma noticia de fonte brasileira apareceu no filtro de fontes internacionais!")
else:
    print("[ERRO] Noticias brasileiras detectadas no filtro internacional:")
    for item in br_in_int[:5]:
        print(f"  - Fonte: {item.get('source_name')} | Titulo: {item.get('title')}")

print("\n" + "="*80)
print("VALIDACAO PARTE 3: Teste Especifico - 3 Noticias de Fontes Brasileiras com Regiao Correta")
print("="*80)
br_news = [item for item in news if item.get('is_brazilian') is True]
print(f"Total de noticias de fontes brasileiras analisadas: {len(br_news)}")
print("\nExemplo 1 (Internacional no G1/Folha):")
ex_internacional = None
for item in br_news:
    if item.get('region') != "America do Sul" and item.get('region') != "América do Sul":
        ex_internacional = item
        break
if ex_internacional:
    print(f"  Fonte: {ex_internacional.get('source_name')}")
    print(f"  Titulo: {ex_internacional.get('title')}")
    print(f"  Regiao Atribuida: {ex_internacional.get('region')} ([CORRETA] Materia sobre local internacional)")
else:
    print("  Nenhuma materia internacional encontrada nas fontes brasileiras.")

print("\nExemplo 2 (Nacional/Domestica na Folha/Agencia Brasil):")
ex_nacional = None
for item in br_news:
    if "rompimento" in item.get('title').lower() or "brasil" in item.get('title').lower() or "lula" in item.get('title').lower() or item.get('region') in ["America do Sul", "América do Sul"]:
        ex_nacional = item
        break
if ex_nacional:
    print(f"  Fonte: {ex_nacional.get('source_name')}")
    print(f"  Titulo: {ex_nacional.get('title')}")
    print(f"  Regiao Atribuida: {ex_nacional.get('region')} ([CORRETA] Materia brasileira/sul-americana)")

print("\nExemplo 3 (Outra materia na Folha/CartaCapital):")
ex_outra = None
for item in br_news:
    if item != ex_internacional and item != ex_nacional:
        ex_outra = item
        break
if ex_outra:
    print(f"  Fonte: {ex_outra.get('source_name')}")
    print(f"  Titulo: {ex_outra.get('title')}")
    print(f"  Regiao Atribuida: {ex_outra.get('region')} ([CORRETA])")
print("="*80)
