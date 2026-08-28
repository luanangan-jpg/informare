# Informare — "O mundo em um só lugar"

Este é o repositório da nova versão do **Informare**, um agregador de notícias sobre Relações Internacionais 100% automatizado. Ele consome feeds RSS de fontes renomadas, classifica os conteúdos por região e área temática, remove duplicatas e publica uma página estática interativa e responsiva.

---

## 🛠️ Como funciona a automação?

1. **Agendador (GitHub Actions)**: A cada hora, o GitHub executa silenciosamente o arquivo `.github/workflows/update-news.yml`.
2. **Coletor e Curador (`fetch_news.py`)**: O script em Python realiza:
   * Conexão paralela com mais de 15 fontes de notícias de grande renome.
   * Extração de imagens (RSS, `enclosure` ou extração inteligente de tag `og:image` do site original).
   * Mapeamento rígido de fontes brasileiras para a região **América do Sul**.
   * Classificação regional e temática das fontes internacionais baseada em heurísticas e palavras-chave.
   * Deduplicação inteligente de notícias redundantes.
   * Atualização das estatísticas de controle.
3. **Persistência (`data/news.json`)**: O script gera os resultados no arquivo JSON. O robô do GitHub faz o commit e push automáticos para este repositório.
4. **Exibição (`index.html`)**: O frontend em HTML/CSS/JS (com Tailwind CSS) carrega esse arquivo `news.json` e renderiza os cards, o carrossel de destaques e aplica os filtros e busca em tempo real sem recarregar a página.

---

## 🚀 Como publicar seu site no GitHub (Passo a Passo Simples)

Como você solicitou que o site seja publicado sem precisar programar nada, siga estes passos simples:

### Passo 1: Criar o Repositório no GitHub
1. Acesse o seu [GitHub](https://github.com/) (crie uma conta gratuita se não tiver).
2. Clique no botão verde **New** (ou acesse `https://github.com/new`).
3. Dê o nome de **`informare`** ao repositório.
4. Deixe o repositório marcado como **Public** (Público) — isso é essencial para que o GitHub Pages funcione gratuitamente.
5. **Não** selecione nenhuma caixa de criação de README, .gitignore ou licença (deixe o repositório completamente vazio).
6. Clique em **Create repository**.

### Passo 2: Fazer o Upload dos Arquivos
Você pode enviar os arquivos usando o terminal do Git ou diretamente pela interface do site do GitHub (se preferir arrastar e soltar):

**Opção A — Pelo terminal (Recomendado se tiver o Git instalado):**
Abra o prompt de comando (PowerShell/CMD) na pasta deste projeto e digite os comandos:
```bash
git init
git add .
git commit -m "first commit: informare v2"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/informare.git
git push -u origin main
```
*(Substitua `SEU_USUARIO` pelo seu nome de usuário do GitHub).*

**Opção B — Pelo site do GitHub (Sem instalar nada):**
1. Na página do repositório recém-criado, clique no link que diz **"uploading an existing file"** (enviar um arquivo existente).
2. Arraste todos os arquivos e pastas da sua pasta local `C:\Users\Dell\.gemini\antigravity\scratch\informare-curadoria` (inclusive a pasta oculta `.github` e a pasta `data`) para a área de upload.
3. Clique em **Commit changes** na parte inferior.

### Passo 3: Ativar o GitHub Pages (Publicação do Site)
1. No seu repositório no GitHub, clique na aba **Settings** (Configurações) no menu superior.
2. Na barra lateral esquerda, clique em **Pages** (dentro da seção "Code and automation").
3. Em **Build and deployment**, onde diz **Source**, selecione **Deploy from a branch**.
4. Em **Branch**, selecione `main` (ou a sua branch principal) e a pasta `/ (root)`. Clique em **Save**.
5. Em cerca de 1 a 2 minutos, o GitHub exibirá o link público do seu site no topo dessa mesma página (ex: `https://seu-usuario.github.io/informare/`).

### Passo 4: Dar permissão de escrita para a Automação
Como o GitHub Actions precisa salvar o arquivo `news.json` atualizado no seu repositório, você precisa ativar essa permissão:
1. Vá em **Settings** (Configurações) no seu repositório.
2. Na barra lateral esquerda, clique em **Actions** e depois em **General**.
3. Role até o final da página até a seção **Workflow permissions**.
4. Marque a opção **Read and write permissions** (Permissões de leitura e escrita).
5. Clique em **Save**.

Pronto! Agora o seu site está no ar e atualizará sozinho a cada 1 hora!

---

## ✍️ Como adicionar ou remover uma fonte de notícias?

Você pode gerenciar as fontes editando diretamente o arquivo **`fetch_news.py`**:

### Adicionar uma nova fonte:
Procure a lista chamada `SOURCES` (por volta da linha 14) e adicione um novo bloco no seguinte formato:

```python
    {
        "id": "nome_unico_da_fonte",
        "name": "Nome de Exibição",
        "url": "URL_DO_FEED_RSS_AQUI",
        "is_brazilian": True,        # Defina como True se for fonte nacional (para América do Sul)
        "default_region": "América do Sul" # Região padrão se for internacional
    },
```

### Remover uma fonte:
Basta apagar ou comentar (colocando `#` no início das linhas) o bloco da fonte indesejada na lista `SOURCES`.

Depois de salvar as edições, basta enviar as alterações para o GitHub. A automação cuidará de processar o novo feed automaticamente no próximo ciclo.
