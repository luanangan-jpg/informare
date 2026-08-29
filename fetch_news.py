import os
import re
import json
import logging
import urllib.parse
from datetime import datetime, timezone
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import feedparser
import requests
from bs4 import BeautifulSoup

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lista de Fontes
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
        "id": "dw_brasil",
        "name": "DW Brasil",
        "url": "https://rss.dw.com/rdf/rss-br-all",
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
        "id": "onu_news",
        "name": "ONU News",
        "url": "https://news.un.org/feed/subscribe/pt/news/all/rss.xml",
        "is_brazilian": False,
        "default_region": "Global"
    },
    {
        "id": "poder360",
        "name": "Poder360",
        "url": "https://www.poder360.com.br/feed/",
        "is_brazilian": True,
        "default_region": "América do Sul"
    },
    {
        "id": "bbc_world",
        "name": "BBC World News",
        "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "is_brazilian": False,
        "default_region": "Global"
    },
    {
        "id": "dw_english",
        "name": "DW World News",
        "url": "https://rss.dw.com/rdf/rss-en-world",
        "is_brazilian": False,
        "default_region": "Europa"
    },
    {
        "id": "aljazeera_english",
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "is_brazilian": False,
        "default_region": "Oriente Médio"
    },
    {
        "id": "france24",
        "name": "France 24",
        "url": "https://www.france24.com/en/rss",
        "is_brazilian": False,
        "default_region": "Europa"
    },
    {
        "id": "npr",
        "name": "NPR World News",
        "url": "https://feeds.npr.org/1004/rss.xml",
        "is_brazilian": False,
        "default_region": "Global"
    },
    {
        "id": "pbs_newshour",
        "name": "PBS NewsHour",
        "url": "https://www.pbs.org/newshour/feeds/rss/world",
        "is_brazilian": False,
        "default_region": "Global"
    },
    {
        "id": "rtve",
        "name": "RTVE Internacional",
        "url": "https://www.rtve.es/rss/temas_internacional.xml",
        "is_brazilian": False,
        "default_region": "Europa"
    },
    {
        "id": "europa_press",
        "name": "Europa Press",
        "url": "https://www.europapress.es/rss/rss.aspx?ch=00069",
        "is_brazilian": False,
        "default_region": "Europa"
    }
]

# Imagens de Fallback por Categoria
THEME_IMAGES = {
    "Geopolítica e Segurança": [
        "https://images.unsplash.com/photo-1508847154043-be12a62861c1?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1544027993-37dbfe43562a?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1526470608268-f674ce90ebd4?q=80&w=800&auto=format&fit=crop"
    ],
    "Política Internacional": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?q=80&w=800&auto=format&fit=crop"
    ],
    "Política Brasileira": [
        "https://images.unsplash.com/photo-1481349518771-20055b2a7b24?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1620121692029-d088224ddc74?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?q=80&w=800&auto=format&fit=crop"
    ],
    "Economia Internacional": [
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?q=80&w=800&auto=format&fit=crop"
    ],
    "Economia Brasileira": [
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=800&auto=format&fit=crop"
    ],
    "Comércio e Finanças": [
        "https://images.unsplash.com/photo-1578575437130-527eed3abbec?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1522071820081-009f0129c71c?q=80&w=800&auto=format&fit=crop"
    ],
    "Meio Ambiente e Clima": [
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=800&auto=format&fit=crop"
    ],
    "Ciência, Tecnologia e Inovação": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1507668077129-56e32842fceb?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=800&auto=format&fit=crop"
    ],
    "Direitos Humanos, Sociedade e Migrações": [
        "https://images.unsplash.com/photo-1542810634-71277d95dcbb?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1489533119213-66a5cd877091?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1531206715517-5c0ba140e2b8?q=80&w=800&auto=format&fit=crop"
    ],
    "Saúde": [
        "https://images.unsplash.com/photo-1584515901367-f1c2a12a50ea?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1584036561566-baf2418a7c21?q=80&w=800&auto=format&fit=crop"
    ],
    "Direito Internacional e Instituições": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1505664194779-8beaceb93744?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop"
    ],
    "Cultura, Mídia e Sociedade": [
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=800&auto=format&fit=crop"
    ],
    "Outros / Multitemático": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1526470608268-f674ce90ebd4?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1493612276216-ee3925520721?q=80&w=800&auto=format&fit=crop"
    ]
}

def clean_html(text):
    """Remove tags HTML e espaços em branco desnecessários."""
    if not text:
        return ""
    soup = BeautifulSoup(text, 'html.parser')
    plain_text = soup.get_text(separator=' ')
    plain_text = re.sub(r'\s+', ' ', plain_text)
    return plain_text.strip()

def extract_image_from_entry(entry):
    """Extrai imagem dos campos de mídia do RSS ou tag enclosure."""
    if 'media_content' in entry and entry.media_content:
        for media in entry.media_content:
            if 'url' in media and media['url']:
                return media['url']
    if 'media_thumbnail' in entry and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            if 'url' in media and media['url']:
                return media['url']
    if 'enclosures' in entry and entry.enclosures:
        for enc in entry.enclosures:
            if 'type' in enc and enc['type'].startswith('image/') and 'href' in enc:
                return enc['href']
            elif 'href' in enc:
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
            meta_tw = soup.find('meta', name='twitter:image')
            if meta_tw and meta_tw.get('content'):
                return meta_tw['content']
    except Exception as e:
        logging.debug(f"Erro ao buscar og:image para {url}: {e}")
    return None

def extract_loremflickr_query(title):
    """Extrai palavras-chave do título da notícia para busca de imagem no LoremFlickr."""
    clean_title = re.sub(r'[^\w\s]', '', title)
    words = clean_title.lower().split()
    stop_words = {
        "a", "o", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das", "em", "no", "na", 
        "nos", "nas", "para", "com", "por", "que", "e", "ou", "se", "como", "ao", "aos", "à", "às",
        "sobre", "sob", "contra", "entre", "lamenta", "promete", "anuncia", "diz", "vê", "é", "são", "foi", 
        "foram", "será", "serão", "tem", "têm", "tinha", "tinham", "veja", "como", "onde", "quem", "qual", "the", 
        "of", "in", "to", "for", "with", "on", "at", "by", "from", "about", "el", "la", "los", "las", "un", "una",
        "en", "para", "con", "por", "que", "y", "o", "su", "sus", "del", "al", "sobre", "entre", "contra",
        "morre", "morrem", "morte", "mortes", "mata", "matam", "após", "depois", "novo", "nova", "novos", "novas"
    }
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    tags = keywords[:2]
    if not tags:
        return "news"
    return ",".join(tags)

def fetch_loremflickr_fallback_image(title):
    """Busca uma foto real no LoremFlickr por meio de redirecionamento HEAD (ultra-rápido)."""
    query = extract_loremflickr_query(title)
    url = f"https://loremflickr.com/800/600/{query}"
    try:
        response = requests.head(url, allow_redirects=True, timeout=4)
        if response.status_code == 200:
            return response.url
    except Exception as e:
        logging.debug(f"Erro ao buscar LoremFlickr para '{query}': {e}")
    return None

def parse_struct_time(struct_t):
    """Converte time.struct_time do feedparser para string ISO 8601 UTC."""
    if not struct_t:
        return None
    try:
        dt = datetime(
            year=struct_t.tm_year,
            month=struct_t.tm_mon,
            day=struct_t.tm_mday,
            hour=struct_t.tm_hour,
            minute=struct_t.tm_min,
            second=struct_t.tm_sec,
            tzinfo=timezone.utc
        )
        return dt.isoformat().replace("+00:00", "Z")
    except Exception:
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

def classify_region(title, summary, source_info, theme=None):
    """Classifica a notícia por região geográfica baseada no conteúdo, pesando mais o título."""
    t_clean = title.lower()
    s_clean = summary.lower()
    
    terms = {
        "América do Norte": [
            "eua", "estados unidos", "united states", "usa", "us", "washington", "nova york", "new york", "biden", "trump", "kamala", 
            "harris", "canada", "canadá", "ottawa", "trudeau", "mexico", "méxico", "obrador", "sheinbaum", "mexico city",
            "americano", "americana", "americanos", "americanas", "american", "canadense", "canadenses", "canadian",
            "mexicano", "mexicana", "mexicanos", "mexicanas", "mexican", "casa branca", "white house", "pentágono", "pentagon"
        ],
        "América Central": [
            "cuba", "havana", "haiti", "guatemala", "honduras", "nicaragua", "nicarágua", "costa rica", 
            "panama", "panamá", "jamaica", "bahamas", "el salvador", "bukele",
            "cubano", "cubana", "cubanos", "cubanas", "cuban", "haitiano", "haitiana", "haitianos", "haitianas", "haitian",
            "nicaraguan", "salvadoran", "panamanian"
        ],
        "América do Sul": [
            "brasil", "brazil", "brasília", "lula", "argentina", "buenos aires", "milei", "venezuela", "caracas", 
            "maduro", "colombia", "colômbia", "petro", "chile", "santiago", "boric", "peru", "lima", 
            "bolivia", "bolívia", "equador", "paraguai", "uruguai", "guiana", "suriname",
            "brasileiro", "brasileira", "brasileiros", "brasileiras", "brazilian", "argentino", "argentina", 
            "argentinos", "argentinas", "argentinian", "venezuelano", "venezuelana", "venezuelanos", "venezuelanas", "venezuelan",
            "colombiano", "colombiana", "colombianos", "colombianas", "colombian", "chileno", "chilena", 
            "chilenos", "chilenas", "chilean", "peruano", "peruana", "peruanos", "peruanas", "peruvian",
            "ecuadorian", "bolivian", "paraguayan", "uruyan"
        ],
        "Europa": [
            "europa", "europe", "união europeia", "european union", "eu", "alemanha", "germany", "berlim", "berlin", "scholz", "german", "frança", "france", "paris", "macron", "french",
            "reino unido", "united kingdom", "uk", "inglaterra", "england", "londres", "london", "starmer", "british", "english", "itália", "italy", "roma", "rome", "meloni", "italian", "espanha", "spain",
            "madri", "madrid", "sánchez", "spanish", "portugal", "lisboa", "lisbon", "portuguese", "rússia", "russia", "moscou", "moscow", "putin", "russian", "ucrânia", "ukraine",
            "kiev", "kyiv", "zelensky", "ukrainian", "bruxelas", "brussels", "suíça", "switzerland", "suécia", "sweden", "noruega", "norway", "finlândia", "finland", "polônia", "poland",
            "grécia", "greece", "irlanda", "ireland", "europeu", "europeia", "europeus", "europeias", "alemão", "alemã", 
            "alemães", "francês", "francesa", "franceses", "francesas", "britânico", "britânica", 
            "britânicos", "britânicas", "inglês", "inglesa", "ingleses", "inglesas", "italiano", 
            "italiana", "italianos", "italianas", "espanhol", "espanhola", "espanhóis", "espanholas", 
            "português", "portuguesa", "portugueses", "portuguesas", "russo", "russa", "russos", 
            "russas", "ucraniano", "ucraniana", "ucranianos", "ucranianas"
        ],
        "Ásia": [
            "ásia", "asia", "asian", "china", "pequim", "beijing", "xi jinping", "chinese", "japão", "japan", "tóquio", "tokyo", "japanese", "coreia", "korea", "seul", "seoul", "korean",
            "pyongyang", "kim jong", "índia", "india", "nova deli", "new delhi", "modi", "indian", "vietnã", "vietnam", "vietnamese", "indonésia", "indonesia", "indonesian",
            "filipinas", "philippines", "filipino", "paquistão", "pakistan", "pakistani", "taiwan", "taipei", "taiwanese", "chinês", "chinesa", "chineses", "chinesas", 
            "japonês", "japonesa", "japoneses", "japonesas", "coreano", "coreana", "coreanos", "coreanas", 
            "indiano", "indiana", "indianos", "indianas", "nepal", "tibete", "tibet", "tibetan", "himalaia", "himalayas", "tailândia", "thailand",
            "tailandia", "singapura", "singapore", "vietna", "paquistan", "nepalês", "nepalesa", "tibetano", "tibetana"
        ],
        "Oriente Médio": [
            "oriente médio", "middle east", "israel", "israeli", "tel aviv", "jerusalém", "jerusalem", "netanyahu", "palestina", "palestine", "gaza", "palestinian",
            "hamas", "irã", "iran", "teerã", "tehran", "iranian", "arábia saudita", "saudi arabia", "saudi", "riad", "riyadh", "síria", "syria", "syrian", "damascus", "iêmen", "yemen", "yemeni", "líbano", "lebanon", "lebanese", "beirute", "beirut",
            "hezbollah", "iraque", "iraq", "iraqi", "baghdad", "turquia", "turkey", "turkish", "ancara", "ankara", "erdogan", "catar", "qatar", "doha",
            "israelense", "israelenses", "palestino", "palestina", "palestinos", "palestinas", 
            "iraniano", "iraniana", "iranianos", "iranianas", "turco", "turca", "turcos", "turcas", 
            "saudita", "sauditas"
        ],
        "África": [
            "áfrica", "africa", "african", "áfrica do sul", "south africa", "south african", "egito", "egypt", "egyptian", "cairo", "nigéria", "nigeria", "nigerian", "abuja", "quênia", "kenya", "kenyan",
            "nairóbi", "nairobi", "etiópia", "ethiopia", "ethiopian", "líbia", "libya", "libyan", "argélia", "algeria", "algerian", "marrocos", "morocco", "moroccan", "rabat", "angola", "angolan", "luanda", 
            "moçambique", "mozambique", "maputo", "sudão", "sudan", "sudanese", "khartoum", "gana", "ghana", "senegal", "senegalese", "rdc", "congo",
            "africano", "africana", "africanos", "africanas", "egípcio", "egípcia", "egípcios", "egípcias", 
            "angolano", "angolana", "angolanos", "angolanas", "sul-africano", "sul-africana"
        ],
        "Oceania": [
            "oceania", "austrália", "australia", "australian", "camberra", "canberra", "nova zelândia", "new zealand", "wellington", "kiwi",
            "australiano", "australiana", "australianos", "australianas"
        ]
    }
    
    # Contagem ponderada de ocorrências
    scores = {region: 0 for region in terms}
    for region, keywords in terms.items():
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            # Título tem peso 5 por correspondência
            t_matches = len(re.findall(pattern, t_clean))
            # Resumo tem peso 1 por correspondência
            s_matches = len(re.findall(pattern, s_clean))
            
            scores[region] += (t_matches * 5) + s_matches
            
    # Filtra as regiões com maior pontuação
    max_score = 0
    best_region = None
    for region, score in scores.items():
        if score > max_score:
            max_score = score
            best_region = region
            
    # Se não houver correspondência clara na matéria
    if best_region is None:
        # Se o tema for inerentemente sobre o Brasil, classifica na América do Sul
        if theme in ["Política Brasileira", "Economia Brasileira"]:
            return "América do Sul"
        # Se a fonte for brasileira e não houver menção explícita de outra região, assume América do Sul como padrão
        if source_info.get("is_brazilian"):
            return "América do Sul"
        return source_info.get("default_region", "Global")
        
    return best_region

def classify_theme(title, summary, source_info):
    """Classifica a notícia por área temática, dando mais peso ao título."""
    t_clean = title.lower()
    s_clean = summary.lower()
    content = (title + " " + summary).lower()
    
    categories = {
        "Geopolítica e Segurança": [
            "guerra", "conflito", "exército", "míssil", "mísseis", "armas", "otan", "defesa", "forças armadas", "bombardeio", "ataque", "invasão", "militar", "geopolítica", "ciberataque", "espionagem", "nuclear", "terrorismo", "pentágono", "hezbollah", "hamas", "escalada", "tensão", "sanções",
            "war", "conflict", "army", "military", "missile", "missiles", "weapons", "defense", "forces", "bombing", "attack", "invasion", "cyberattack", "espionage", "terror", "tensions", "sanctions",
            "conflicto", "ejército", "misil", "defensa", "fuerzas", "bombardeo", "invasión", "sanciones"
        ],
        "Política Internacional": [
            "eleições", "eleição", "presidente", "chanceler", "diplomacia", "embaixada", "tratado", "acordo bilateral", "líderes", "cúpula", "visita oficial", "parlamento", "governo estrangeiro", "putin", "biden", "trump", "kamala", "macron", "governo de", "premiê", "primeiro-ministro", "parlamentar", "votação", "decreto",
            "election", "elections", "president", "chancellor", "diplomacy", "embassy", "treaty", "summit", "parliament", "government", "prime minister", "senate", "house of representatives", "cabinet",
            "elecciones", "elección", "chanciller", "embajada", "cumbre", "gobierno", "primer ministro"
        ],
        "Política Brasileira": [
            "lula", "itamaraty", "diplomacia brasileira", "governo brasileiro", "ministério das relações exteriores", "congresso brasileiro", "brasília", "planalto", "mre", "mauro vieira",
            "stf", "supremo tribunal", "alexandre de moraes", "congresso", "senado", "câmara dos deputados", "câmara federal", "parlamentar", "votação", "tse", "pf", "polícia federal", "plenário", "bolsonaro", "ministro do stf", "agu", "pgr", "palácio do planalto", "esplanada", "governadores", "senador", "deputado"
        ],
        "Economia Internacional": [
            "fed", "federal reserve", "banco central europeu", "bce", "inflação nos estados unidos", "pib da china", "crise na argentina", "eurozona", "wall street", "juros", "inflação", "banco central", "fmi", "banco mundial",
            "ecb", "inflation", "gdp", "central bank", "recession", "economic", "imf", "world bank", "interest rates",
            "inflación", "pib", "banco central", "recesión", "crisis"
        ],
        "Economia Brasileira": [
            "selic", "banco central do brasil", "haddad", "ministério da fazenda", "ipca", "pib brasileiro", "economia brasileira", "mercado financeiro brasileiro", "arcabouço fiscal", "receita federal", "arcabouço", "tributária", "déficit", "superávit", "bndes", "reforma tributária"
        ],
        "Comércio e Finanças": [
            "exportação", "importação", "comércio exterior", "tarifas", "mercosul", "acordo comercial", "câmbio", "dólar", "euro", "bolsa de valores", "bovespa", "omc", "comercial", "finanças", "taxação",
            "exports", "imports", "trade", "tariffs", "dollar", "stocks", "market", "finance", "commercial",
            "exportación", "importación", "aranceles", "dólar", "bolsa"
        ],
        "Meio Ambiente e Clima": [
            "cop", "aquecimento global", "mudança climática", "mudanças climáticas", "desmatamento", "sustentabilidade", "carbono", "poluição", "energias renováveis", "solar", "eólica", "floresta", "desastre natural", "enchentes", "seca", "amazônia", "meio ambiente", "desastre", "clima", "chuvas", "tempestade", "incêndios",
            "climate", "warming", "deforestation", "sustainability", "carbon", "pollution", "renewable", "wind", "forest", "flood", "drought", "environment", "storm",
            "calentamiento", "deforestación", "contaminación", "renovable", "inundación", "sequía", "medio ambiente", "clima"
        ],
        "Ciência, Tecnologia e Inovação": [
            "inteligência artificial", " ia ", "tecnologia", "semicondutores", "chips", "espacial", "nasa", "internet", "redes sociais", "inovação", "ciência", "pesquisa", "telescópio", "cibersegurança", "algoritmo", "openai", "google", "meta",
            "artificial intelligence", " ai ", "technology", "semiconductors", "space", "innovation", "science", "research", "cybersecurity", "algorithm",
            "tecnología", "innovación", "ciencia", "investigación", "algoritmo"
        ],
        "Direitos Humanos, Sociedade e Migrações": [
            "refugiados", "migração", "imigrantes", "direitos humanos", "protesto", "manifestação", "racismo", "gênero", "direitos civis", "desigualdade", "pobreza", "discriminação", "ativistas", "fome",
            "refugees", "migration", "migrants", "human rights", "protest", "racism", "gender", "civil rights", "inequality", "poverty", "famine",
            "refugiados", "migración", "derechos humanos", "protesta"
        ],
        "Saúde": [
            "oms", "saúde pública", "vacina", "vacinação", "pandemia", "vírus", "mpox", "covid", "gripe", "surto", "vigilância sanitária", "doença", "medicamento", "saúde global",
            "who", "vaccine", "vaccination", "pandemic", "virus", "outbreak", "disease", "health",
            "vacuna", "pandemia", "salud"
        ],
        "Direito Internacional e Instituições": [
            "onu", "nações unidas", "tribunal de haia", "tpi", "corte internacional", "resoluções", "conselho de segurança", "oea", "tratado internacional", "direitos internacionais",
            "un", "united nations", "icc", "hague", "security council",
            "naciones unidas", "consejo de seguridad"
        ],
        "Cultura, Mídia e Sociedade": [
            "cinema", "festival", "música", "literatura", "esporte", "olimpíadas", "copa do mundo", "imprensa", "jornalismo", "patrimônio cultural", "artes", "show", "cultura",
            "music", "sports", "olympics", "world cup", "press", "journalism", "arts", "culture",
            "música", "deportes", "prensa", "periodismo", "artes", "cultura"
        ]
    }
    
    scores = {cat: 0 for cat in categories}
    for cat, keywords in categories.items():
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            # Título tem peso 5 por correspondência
            t_matches = len(re.findall(pattern, t_clean))
            # Resumo tem peso 1 por correspondência
            s_matches = len(re.findall(pattern, s_clean))
            scores[cat] += (t_matches * 5) + s_matches
            
    max_score = 0
    best_category = "Outros / Multitemático"
    
    for cat, score in scores.items():
        if score > max_score:
            max_score = score
            best_category = cat
            
    # Validações cruzadas de economia / política nacional vs internacional baseada nas fontes e termos
    if best_category in ["Economia Internacional", "Economia Brasileira", "Política Internacional", "Política Brasileira"]:
        is_source_brazilian = source_info.get("is_brazilian", False)
        # Verifica se há palavras chaves internacionais fortes na matéria
        has_intl_keywords = any(kw in content for kw in ["eua", "usa", "trump", "biden", "china", "pequim", "rússia", "ucrânia", "putin", "europa", "frança", "macron", "alemanha", "reino unido", "argentina", "milei", "venezuela", "maduro"])
        
        if is_source_brazilian and not has_intl_keywords:
            if best_category == "Economia Internacional":
                best_category = "Economia Brasileira"
            elif best_category == "Política Internacional":
                best_category = "Política Brasileira"
        elif not is_source_brazilian:
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
                # Critério de substituição: prefere o que tem imagem real
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
                
            # Extrai e normaliza data de publicação (prioriza struct_time pré-processada pelo feedparser)
            pub_date_struct = getattr(entry, 'published_parsed', getattr(entry, 'updated_parsed', None))
            if pub_date_struct:
                pub_date = parse_struct_time(pub_date_struct)
            else:
                pub_date_raw = getattr(entry, 'published', getattr(entry, 'updated', None))
                pub_date = parse_date(pub_date_raw)
            
            # Classificações
            theme = classify_theme(title, summary, source)
            region = classify_region(title, summary, source, theme)
            
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
    
    # Comentário de Prevenção/Controle:
    # Valida se todas as fontes possuem as chaves necessárias configuradas de forma explícita na lista SOURCES.
    for src in SOURCES:
        required_keys = ["id", "name", "url", "is_brazilian", "default_region"]
        missing = [k for k in required_keys if k not in src]
        if missing:
            logging.error(f"FONTE DESCONFIGURADA DETECTADA: {src.get('name', 'Sem Nome')}. Chaves faltando: {missing}")
            raise ValueError(f"Fonte incompleta na tabela de mapeamento: {src}")
            
    # Carrega notícias pré-existentes do cache JSON local (para histórico cumulativo)
    existing_news = []
    output_dir = 'data'
    output_path = os.path.join(output_dir, 'news.json')
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                existing_news = old_data.get('news', [])
                logging.info(f"Carregadas {len(existing_news)} notícias pré-existentes do cache local.")
        except Exception as e:
            logging.warning(f"Não foi possível carregar notícias pré-existentes: {e}")

    all_news = []
    
    # Coleta concorrente dos feeds RSS
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_single_feed, src): src for src in SOURCES}
        for future in as_completed(futures):
            all_news.extend(future.result())
            
    logging.info(f"Coleta de RSS finalizada. Total bruto de notícias novas: {len(all_news)}")
    
    # Mescla notícias recém-coletadas com as notícias históricas em cache
    combined_news = all_news + existing_news
    
    # Remove duplicatas (preservando o primeiro registro e a data real original)
    combined_news = deduplicate_news(combined_news)
    logging.info(f"Total após mesclagem e deduplicação: {len(combined_news)}")
    
    # Busca concorrente de og:image para as notícias que ainda não têm imagem de capa (limite de 30 para economizar recursos)
    news_needing_image = [item for item in combined_news if not item['image_url']][:30]
    if news_needing_image:
        logging.info(f"Buscando og:image nas páginas originais de {len(news_needing_image)} matérias...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures_og = {executor.submit(fetch_og_image, item['link']): item for item in news_needing_image}
            for future in as_completed(futures_og):
                item = futures_og[future]
                og_img = future.result()
                if og_img:
                    item['image_url'] = og_img
                
    # Depois de tentar og:image, para as matérias que continuarem sem imagem, busca fallback no LoremFlickr (limite de 25 para evitar lentidão)
    news_still_needing_image = [item for item in combined_news if not item['image_url']][:25]
    if news_still_needing_image:
        logging.info(f"Buscando fallback de imagem no LoremFlickr para {len(news_still_needing_image)} matérias...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures_uns = {executor.submit(fetch_loremflickr_fallback_image, item['title']): item for item in news_still_needing_image}
            for future in as_completed(futures_uns):
                item = futures_uns[future]
                lorem_img = future.result()
                if lorem_img:
                    item['image_url'] = lorem_img

    # Ordena notícias por data de publicação real (mais recentes primeiro)
    combined_news.sort(key=lambda x: x['published_at'], reverse=True)
    
    # Estatísticas de validação
    theme_counts = {}
    region_counts = {}
    for item in combined_news[:150]:
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
        "news": combined_news[:150]  # Armazena as 150 notícias mais recentes
    }
    
    # Cria o diretório de saída se não existir
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    logging.info(f"Notícias salvas com sucesso em: {output_path}")
    logging.info(f"Tempo total de execução: {time.time() - start_time:.2f} segundos")

if __name__ == '__main__':
    main()
