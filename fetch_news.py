import os
import re
import json
import logging
import urllib.parse
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import feedparser
import requests
from bs4 import BeautifulSoup

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lista de Fontes
# Cada fonte possui um identificador, nome, URL do feed RSS, se é brasileira, e região padrão (caso BR)
SOURCES = [
    {
        "id": "agencia_brasil",
        "name": "Agência Brasil",
        "url": "https://agenciabrasil.ebc.com.br/rss/internacional/feed.xml",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "g1_mundo",
        "name": "G1 Mundo",
        "url": "https://g1.globo.com/dinamico/us/rss/globo/mundo/index.xml",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "cnn_brasil",
        "name": "CNN Brasil",
        "url": "https://www.cnnbrasil.com.br/internacional/feed/",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "bbc_brasil",
        "name": "BBC News Brasil",
        "url": "https://feeds.bbci.co.uk/portuguese/rss.xml",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "estadao_inter",
        "name": "Estadão",
        "url": "https://www.estadao.com.br/arc/outboundfeeds/rss/category/internacional/",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "folha_mundo",
        "name": "Folha de S.Paulo",
        "url": "https://feeds.folha.uol.com.br/mundo/rss091.xml",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "correio_braziliense",
        "name": "Correio Braziliense",
        "url": "https://www.correiobraziliense.com.br/rss/mundo/rss.xml",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "carta_capital",
        "name": "CartaCapital",
        "url": "https://www.cartacapital.com.br/mundo/feed/",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "exame_mundo",
        "name": "Exame",
        "url": "https://exame.com/bussiness/mundo/feed/",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "valor_mundo",
        "name": "Valor Econômico",
        "url": "https://valor.globo.com/rss/mundo/",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "elpais_brasil",
        "name": "El País Brasil",
        "url": "https://brasil.elpais.com/rss/brasil/portada.xml",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "dw_brasil",
        "name": "DW Brasil",
        "url": "https://rss.dw.com/rdf/rss-br-all",
        "is_brazilian": False,
        "default_region": "Europa"
    },
    {
        "id": "le_monde_diplomatique",
        "name": "Le Monde Diplomatique Brasil",
        "url": "https://diplomatique.org.br/feed/",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "onu_news",
        "name": "ONU News",
        "url": "https://news.un.org/feed/subscribe/pt/news/all/rss.xml",
        "is_brazilian": False,
        "default_region": "Global"
    },
    {
        "id": "jornal_negocios",
        "name": "Jornal de Negócios",
        "url": "https://www.jornaldenegocios.pt/rss",
        "is_brazilian": False,
        "default_region": "Europa"
    },
    {
        "id": "publico_portugal",
        "name": "Público",
        "url": "https://www.publico.pt/nos/rss/mundo",
        "is_brazilian": False,
        "default_region": "Europa"
    },
    {
        "id": "rfi_brasil",
        "name": "RFI Brasil",
        "url": "https://www.rfi.fr/br/geral/rss",
        "is_brazilian": False,
        "default_region": "Europa"
    },
    {
        "id": "efe_agro",
        "name": "EFE Agro",
        "url": "https://efe.com.br/category/mundo/feed/",
        "is_brazilian": False,
        "default_region": "Europa"
    }
]

# Imagens de Fallback por Categoria (Curadoria de fotos reais da Unsplash)
THEME_IMAGES = {
    "Geopolítica e Segurança": [
        "https://images.unsplash.com/photo-1508847154043-be12a62861c1?q=80&w=800&auto=format&fit=crop", # Mapa/militar
        "https://images.unsplash.com/photo-1544027993-37dbfe43562a?q=80&w=800&auto=format&fit=crop", # Arame farpado/fronteira
        "https://images.unsplash.com/photo-1526470608268-f674ce90ebd4?q=80&w=800&auto=format&fit=crop"  # Painel de controle
    ],
    "Política Internacional": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?q=80&w=800&auto=format&fit=crop", # Bandeiras internacionais
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop", # Globo digital
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=80&w=800&auto=format&fit=crop"  # Palanque/tribuna
    ],
    "Política Brasileira": [
        "https://images.unsplash.com/photo-1481349518771-20055b2a7b24?q=80&w=800&auto=format&fit=crop", # Congresso
        "https://images.unsplash.com/photo-1620121692029-d088224ddc74?q=80&w=800&auto=format&fit=crop", # Arte abstrata amarela e verde
        "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?q=80&w=800&auto=format&fit=crop"  # Vista de Brasília
    ],
    "Economia Internacional": [
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=800&auto=format&fit=crop", # Dólares
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop", # Gráficos financeiros
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=800&auto=format&fit=crop"  # Bolsa de valores
    ],
    "Economia Brasileira": [
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800&auto=format&fit=crop", # Moedas/Real
        "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?q=80&w=800&auto=format&fit=crop", # Mercado de São Paulo
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=800&auto=format&fit=crop"  # Finanças
    ],
    "Comércio e Finanças": [
        "https://images.unsplash.com/photo-1578575437130-527eed3abbec?q=80&w=800&auto=format&fit=crop", # Porto/Containers
        "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=800&auto=format&fit=crop", # Logística de comércio
        "https://images.unsplash.com/photo-1522071820081-009f0129c71c?q=80&w=800&auto=format&fit=crop"  # Reunião de negócios
    ],
    "Meio Ambiente e Clima": [
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=800&auto=format&fit=crop", # Floresta/Montanha
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?q=80&w=800&auto=format&fit=crop", # Terra seca
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=800&auto=format&fit=crop"  # Painel solar/Turbinas
    ],
    "Ciência, Tecnologia e Inovação": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800&auto=format&fit=crop", # Placa de circuito
        "https://images.unsplash.com/photo-1507668077129-56e32842fceb?q=80&w=800&auto=format&fit=crop", # Tecnologia/IA
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=800&auto=format&fit=crop"  # Espaço/Satélite
    ],
    "Direitos Humanos, Sociedade e Migrações": [
        "https://images.unsplash.com/photo-1542810634-71277d95dcbb?q=80&w=800&auto=format&fit=crop", # Refugiados/cerca
        "https://images.unsplash.com/photo-1489533119213-66a5cd877091?q=80&w=800&auto=format&fit=crop", # Protesto/Paz
        "https://images.unsplash.com/photo-1531206715517-5c0ba140e2b8?q=80&w=800&auto=format&fit=crop"  # Mão humana/Igualdade
    ],
    "Saúde": [
        "https://images.unsplash.com/photo-1584515901367-f1c2a12a50ea?q=80&w=800&auto=format&fit=crop", # Hospital/Vacina
        "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?q=80&w=800&auto=format&fit=crop", # Estetoscópio
        "https://images.unsplash.com/photo-1584036561566-baf2418a7c21?q=80&w=800&auto=format&fit=crop"  # Laboratório/Ciência médica
    ],
    "Direito Internacional e Instituições": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=800&auto=format&fit=crop", # Martelo de tribunal/Lei
        "https://images.unsplash.com/photo-1505664194779-8beaceb93744?q=80&w=800&auto=format&fit=crop", # Biblioteca antiga
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop"  # Símbolo multilateral/Globo
    ],
    "Cultura, Mídia e Sociedade": [
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?q=80&w=800&auto=format&fit=crop", # Microfone/Mídia
        "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?q=80&w=800&auto=format&fit=crop", # Artes/Pintura
        "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop"  # Cinema/Cultura
    ],
    "Outros / Multitemático": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop", # Globo
        "https://images.unsplash.com/photo-1526470608268-f674ce90ebd4?q=80&w=800&auto=format&fit=crop", # Fluxo de dados
        "https://images.unsplash.com/photo-1493612276216-ee3925520721?q=80&w=800&auto=format&fit=crop"  # Abstrato elegante
    ]
}

def clean_html(text):
    """Remove tags HTML e espaços em branco desnecessários."""
    if not text:
        return ""
    # Remove tags HTML usando BS4
    soup = BeautifulSoup(text, 'html.parser')
    plain_text = soup.get_text(separator=' ')
    # Remove múltiplos espaços
    plain_text = re.sub(r'\s+', ' ', plain_text)
    return plain_text.strip()

def extract_image_from_entry(entry):
    """Extrai imagem dos campos de mídia do RSS ou tag enclosure."""
    # 1. Campo media:content ou media:thumbnail
    if 'media_content' in entry and entry.media_content:
        for media in entry.media_content:
            if 'url' in media and media['url']:
                return media['url']
    if 'media_thumbnail' in entry and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            if 'url' in media and media['url']:
                return media['url']

    # 2. Campo enclosure
    if 'enclosures' in entry and entry.enclosures:
        for enc in entry.enclosures:
            if 'type' in enc and enc['type'].startswith('image/') and 'href' in enc:
                return enc['href']
            elif 'href' in enc:
                # Fallback se não tiver tipo mas for extensão de imagem
                href = enc['href'].lower()
                if any(ext in href for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                    return enc['href']
    
    return None

def fetch_og_image(url):
    """Busca a tag og:image da página original da matéria."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_og = soup.find('meta', property='og:image')
            if meta_og and meta_og.get('content'):
                return meta_og['content']
            # Fallback para twitter:image
            meta_tw = soup.find('meta', name='twitter:image')
            if meta_tw and meta_tw.get('content'):
                return meta_tw['content']
    except Exception as e:
        logging.debug(f"Erro ao buscar og:image para {url}: {e}")
    return None

def parse_date(date_str):
    """Normaliza datas de publicação para ISO format."""
    if not date_str:
        return datetime.utcnow().isoformat() + "Z"
    
    # Lista de formatos comuns
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M"
    ]
    
    # Tratamentos manuais comuns para fusos horários brasileiros/portugueses
    date_str_clean = date_str.replace("GMT", "+0000").replace("UTC", "+0000").strip()
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str_clean, fmt)
            return dt.isoformat() + "Z"
        except ValueError:
            continue
            
    # Se falhar, usa feedparser parser embutido
    try:
        parsed_t = feedparser._parse_date(date_str)
        if parsed_t:
            dt = datetime(*parsed_t[:6])
            return dt.isoformat() + "Z"
    except Exception:
        pass
        
    return datetime.utcnow().isoformat() + "Z"

def classify_region(title, summary, source_info):
    """Classifica a notícia por região geográfica."""
    # Se for fonte brasileira, força para América do Sul de forma rígida
    if source_info.get("is_brazilian", False):
        return "América do Sul"
        
    content = (title + " " + summary).lower()
    
    # Dicionário de termos
    terms = {
        "América do Norte": ["eua", "estados unidos", "united states", "washington", "nova york", "biden", "trump", "kamala", "canada", "canadá", "ottawa", "trudeau", "mexico", "méxico", "obrador", "sheinbaum"],
        "América Central": ["cuba", "havana", "haiti", "guatemala", "honduras", "nicaragua", "nicarágua", "costa rica", "panama", "panamá", "jamaica", "bahamas", "el salvador", "bukele"],
        "América do Sul": ["brasil", "brasília", "lula", "argentina", "buenos aires", "milei", "venezuela", "caracas", "maduro", "colombia", "colômbia", "petro", "chile", "santiago", "boric", "peru", "lima", "bolivia", "bolívia", "equador", "paraguai", "uruguai", "guiana", "suriname"],
        "Europa": ["europa", "união europeia", "alemanha", "berlim", "scholz", "frança", "paris", "macron", "reino unido", "inglaterra", "londres", "starmer", "itália", "roma", "meloni", "espanha", "madri", "sánchez", "portugal", "lisboa", "rússia", "russia", "moscou", "putin", "ucrânia", "kiev", "zelensky", "bruxelas", "suíça", "suécia", "noruega", "finlândia", "polônia", "grécia", "irlanda"],
        "Ásia": ["ásia", "asia", "china", "pequim", "xi jinping", "japão", "tóquio", "coreia", "seul", "pyongyang", "kim jong", "índia", "india", "nova deli", "modi", "vietnã", "indonésia", "filipinas", "paquistão", "taiwan", "taipei"],
        "Oriente Médio": ["oriente médio", "israel", "tel aviv", "jerusalém", "netanyahu", "palestina", "gaza", "hamas", "irã", "teerã", "arábia saudita", "riad", "síria", "iêmen", "líbano", "beirute", "hezbollah", "iraque", "turquia", "ancara", "erdogan", "catar", "doha"],
        "África": ["áfrica", "africa", "áfrica do sul", "egito", "cairo", "nigéria", "abuja", "quênia", "nairóbi", "etiópia", "líbia", "argélia", "marrocos", "rabat", "angola", "luanda", "moçambique", "maputo", "sudão", "gana", "senegal", "rdc"],
        "Oceania": ["oceania", "austrália", "australia", "camberra", "nova zelândia", "wellington"]
    }
    
    # Contagem de ocorrências
    scores = {region: 0 for region in terms}
    for region, keywords in terms.items():
        for keyword in keywords:
            # Procura por palavra inteira ou padrão delimitado
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, content))
            scores[region] += matches
            
    # Filtra as regiões com maior pontuação
    max_score = 0
    best_region = "Global"
    
    for region, score in scores.items():
        if score > max_score:
            max_score = score
            best_region = region
            
    # Se não houver correspondência clara, usa a região padrão da fonte internacional ou "Global"
    if max_score == 0:
        return source_info.get("default_region", "Global")
        
    return best_region

def classify_theme(title, summary):
    """Classifica a notícia por área temática."""
    content = (title + " " + summary).lower()
    
    # Categorias e suas palavras-chave
    categories = {
        "Geopolítica e Segurança": ["guerra", "conflito", "exército", "míssil", "mísseis", "armas", "otan", "defesa", "forças armadas", "bombardeio", "ataque", "invasão", "militar", "geopolítica", "ciberataque", "espionagem", "nuclear", "terrorismo", "pentágono"],
        "Política Internacional": ["eleições", "eleição", "presidente", "chanceler", "diplomacia", "embaixada", "tratado", "acordo bilateral", "líderes", "cúpula", "visita oficial", "parlamento", "governo estrangeiro", "putin", "biden", "trump", "macron", "governo de"],
        "Política Brasileira": ["lula", "itamaraty", "diplomacia brasileira", "governo brasileiro", "ministério das relações exteriores", "congresso brasileiro", "brasília", "planalto", "mre", "mauro vieira"],
        "Economia Internacional": ["fed", "federal reserve", "banco central europeu", "bce", "inflação nos estados unidos", "pib da china", "crise na argentina", "eurozona", "wall street"],
        "Economia Brasileira": ["selic", "banco central do brasil", "haddad", "ministério da fazenda", "ipca", "pib brasileiro", "economia brasileira", "mercado financeiro brasileiro", "arcabouço fiscal"],
        "Comércio e Finanças": ["exportação", "importação", "comércio exterior", "tarifas", "mercosul", "acordo comercial", "câmbio", "dólar", "euro", "bolsa de valores", "bovespa", "omc", "comercial", "finanças", "taxação"],
        "Meio Ambiente e Clima": ["cop", "aquecimento global", "mudança climática", "mudanças climáticas", "desmatamento", "sustentabilidade", "carbono", "poluição", "energias renováveis", "solar", "eólica", "floresta", "desastre natural", "enchentes", "seca", "amazônia", "meio ambiente"],
        "Ciência, Tecnologia e Inovação": ["inteligência artificial", " ia ", "tecnologia", "semicondutores", "chips", "espacial", "nasa", "internet", "redes sociais", "inovação", "ciência", "pesquisa", "telescópio", "cibersegurança", "algoritmo", "openai", "google", "meta"],
        "Direitos Humanos, Sociedade e Migrações": ["refugiados", "migração", "imigrantes", "direitos humanos", "protesto", "manifestação", "racismo", "gênero", "direitos civis", "desigualdade", "pobreza", "discriminação", "ativistas", "fome"],
        "Saúde": ["oms", "saúde pública", "vacina", "vacinação", "pandemia", "vírus", "mpox", "covid", "gripe", "surto", "vigilância sanitária", "doença", "medicamento", "saúde global"],
        "Direito Internacional e Instituições": ["onu", "nações unidas", "tribunal de haia", "tpi", "corte internacional", "resoluções", "conselho de segurança", "oea", "tratado internacional", "direitos internacionais"],
        "Cultura, Mídia e Sociedade": ["cinema", "festival", "música", "literatura", "esporte", "olimpíadas", "copa do mundo", "imprensa", "jornalismo", "patrimônio cultural", "artes", "show", "cultura"]
    }
    
    scores = {cat: 0 for cat in categories}
    for cat, keywords in categories.items():
        for keyword in keywords:
            # Usando regex para encontrar palavras completas ou expressões exatas
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, content))
            scores[cat] += matches
            
    # Filtra categoria com maior score
    max_score = 0
    best_category = "Outros / Multitemático"
    
    # Regras de desempate e prioridade
    for cat, score in scores.items():
        if score > max_score:
            max_score = score
            best_category = cat
            
    # Validações cruzadas de economia / política nacional vs internacional
    if best_category in ["Economia Internacional", "Economia Brasileira", "Política Internacional", "Política Brasileira"]:
        # Se contiver 'Lula', 'Itamaraty' ou 'Brasil', inclina para variantes brasileiras
        has_brasil_keywords = any(kw in content for kw in ["brasil", "lula", "itamaraty", "brasileiro", "brasileira"])
        if has_brasil_keywords:
            if best_category == "Economia Internacional":
                best_category = "Economia Brasileira"
            elif best_category == "Política Internacional":
                best_category = "Política Brasileira"
        else:
            if best_category == "Economia Brasileira":
                best_category = "Economia Internacional"
            elif best_category == "Política Brasileira":
                best_category = "Política Internacional"

    return best_category

def jaccard_similarity(str1, str2):
    """Calcula a similaridade de Jaccard entre duas strings de texto."""
    words1 = set(re.findall(r'\w+', str1.lower()))
    words2 = set(re.findall(r'\w+', str2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

def deduplicate_news(news_list):
    """Remove notícias duplicadas ou extremamente similares."""
    deduplicated = []
    for item in news_list:
        is_duplicate = False
        for existing in deduplicated:
            # Compara títulos usando Jaccard Similarity
            similarity = jaccard_similarity(item['title'], existing['title'])
            if similarity > 0.6:  # 60% de similaridade indica forte redundância
                is_duplicate = True
                # Critério de substituição: prefere o que tem imagem real ou é de fonte prioritária
                if not existing['image_url'] and item['image_url']:
                    existing['image_url'] = item['image_url']
                break
        if not is_duplicate:
            deduplicated.append(item)
    return deduplicated

def fetch_single_feed(source):
    """Busca e processa um único feed RSS."""
    news_items = []
    logging.info(f"Processando feed: {source['name']}")
    try:
        feed = feedparser.parse(source['url'])
        if not feed.entries:
            logging.warning(f"Nenhuma notícia encontrada para {source['name']}")
            return news_items
            
        for entry in feed.entries[:15]:  # Pega até 15 notícias mais recentes por feed
            title = getattr(entry, 'title', '').strip()
            link = getattr(entry, 'link', '').strip()
            summary = clean_html(getattr(entry, 'summary', ''))
            
            if not title or not link:
                continue
                
            # Extrai e normaliza data de publicação
            pub_date_raw = getattr(entry, 'published', getattr(entry, 'updated', None))
            pub_date = parse_date(pub_date_raw)
            
            # Classificações
            region = classify_region(title, summary, source)
            theme = classify_theme(title, summary)
            
            # Tenta extrair imagem diretamente do RSS
            image_url = extract_image_from_entry(entry)
            
            news_items.append({
                "title": title,
                "link": link,
                "summary": summary,
                "published_at": pub_date,
                "region": region,
                "theme": theme,
                "source_name": source['name'],
                "source_id": source['id'],
                "is_brazilian": source['is_brazilian'],
                "image_url": image_url,
                "fallback_images": THEME_IMAGES[theme]
            })
    except Exception as e:
        logging.error(f"Erro ao ler feed {source['name']}: {e}")
        
    return news_items

def main():
    start_time = time.time()
    all_news = []
    
    # Coleta concorrente dos feeds RSS
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_single_feed, src): src for src in SOURCES}
        for future in as_completed(futures):
            all_news.extend(future.result())
            
    logging.info(f"Coleta de RSS finalizada. Total bruto de notícias: {len(all_news)}")
    
    # Deduplicação
    all_news = deduplicate_news(all_news)
    logging.info(f"Total após deduplicação: {len(all_news)}")
    
    # Busca concorrente de og:image para as notícias que ainda não têm imagem de capa (limite de 30 para economizar recursos)
    news_needing_image = [item for item in all_news if not item['image_url']][:30]
    logging.info(f"Buscando og:image nas páginas originais de {len(news_needing_image)} matérias...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures_og = {executor.submit(fetch_og_image, item['link']): item for item in news_needing_image}
        for future in as_completed(futures_og):
            item = futures_og[future]
            og_img = future.result()
            if og_img:
                item['image_url'] = og_img
                
    # Ordena notícias por data de publicação (mais recentes primeiro)
    all_news.sort(key=lambda x: x['published_at'], reverse=True)
    
    # Estatísticas de validação
    theme_counts = {}
    region_counts = {}
    for item in all_news:
        theme_counts[item['theme']] = theme_counts.get(item['theme'], 0) + 1
        region_counts[item['region']] = region_counts.get(item['region'], 0) + 1
        
    print("\n--- Estatísticas de Classificação ---")
    print("\nDistribuição por Tema:")
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {theme}: {count}")
    print("\nDistribuição por Região:")
    for region, count in sorted(region_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {region}: {count}")
    print("------------------------------------\n")
    
    # Salva dados coletados em arquivo JSON para o frontend ler
    output_data = {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "news": all_news[:150]  # Armazena as 150 notícias mais recentes
    }
    
    # Cria o diretório de saída se não existir
    os.makedirs('data', exist_ok=True)
    output_path = os.path.join('data', 'news.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    logging.info(f"Notícias salvas com sucesso em: {output_path}")
    logging.info(f"Tempo total de execução: {time.time() - start_time:.2f} segundos")

if __name__ == '__main__':
    main()
