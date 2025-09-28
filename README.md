## Tabela de Conteúdos

- [Visão Geral](#visão-geral)
- [Requisitos](#requisitos)
- [Fluxo do Script](#fluxo-do-script)
- [Trechos Explicados](#trechos-explicados)
  - [Trecho 1 — Imports e configuração inicial](#trecho-1--imports-e-configuração-inicial)
  - [Trecho 2 — Download do HTML e salvar/ler arquivo](#trecho-2--download-do-html-e-salvarler-arquivo)
  - [Trecho 3 — Encontrar `<img alt="Palestrante">` e baixar imagens](#trecho-3--encontrar-img-altpalestrante-e-baixar-imagens)
  - [Trecho 4 — Extrair nome e instituição](#trecho-4--extrair-nome-e-instituição)
  - [Trecho 5 — Extrair e-mail](#trecho-5--extrair-e-mail)
  - [Trecho 6 — Persistir no SQLite](#trecho-6--persistir-no-sqlite)
- [Esquema do Banco](#esquema-do-banco)

---

## Visão Geral

O script:
1. Baixa o HTML de `https://eventos.ifgoiano.edu.br/integra2025/`.
2. Salva em `codigo_fonte.txt` (UTF‑8) e relê como string.
3. Extrai tags `<img alt="Palestrante">` e baixa as imagens.
4. Extrai **nome** (`<h4>...</h4>`) e **instituição** (`<h6>...</h6>`).
5. Extrai **e-mail** (conteúdo de `<p>` dentro de `<div>`).
6. Persiste tudo em `event.db` (tabela `speaker`).

---

## Requisitos

- **Python 3.9+** (recomendado)
- Dependências:
  ```bash
  pip install requests
  ```

---
## Fluxo do Script

- `requests.get(url).text` → obtém HTML como string.
- `open(..., "w"/"r", encoding="utf-8")` → salva e relê o HTML.
- `re.findall()`/`re.search()` → localizam blocos de interesse (imagens, nomes/inst., e-mails).
- `requests.get(url).content` → baixa imagem em bytes; `open(..., "wb")` salva.
- `sqlite3.connect(...); cursor.execute(...); commit(); close()` → cria/insere dados no SQLite.

---

## Trechos Explicados

### Trecho 1 — Imports e configuração inicial

```python
import requests
import re
import sqlite3

url = "https://eventos.ifgoiano.edu.br"
```

**Arquivo**  
Script principal: coleta dados do site e persiste em SQLite.

**O que faz**  
Importa bibliotecas para requisições HTTP, expressões regulares e banco SQLite; define a URL base usada no restante do script.

**Passo a passo**  
1. `import requests` — habilita chamadas HTTP (ex.: `get` para baixar páginas/arquivos).  
2. `import re` — habilita busca/extração de padrões com expressões regulares.  
3. `import sqlite3` — habilita conexão e execução de SQL em banco SQLite local.  
---

### Trecho 2 — Download do HTML e salvar/ler arquivo

```python
codigo_fonte = requests.get(f"{url}/integra2025/")
codigo_fonte_string = codigo_fonte.text

open("codigo_fonte.txt", "w", encoding='utf-8').write(codigo_fonte_string)

arquivo_str = open("codigo_fonte.txt","r", encoding='utf-8').read()
```

**O que faz**  
Baixa o HTML da página do evento, grava em `codigo_fonte.txt` e relê o conteúdo como string para processamento.

**Passo a passo**  
1. `requests.get(f"{url}/integra2025/")` — executa HTTP GET e retorna um `Response`.  
2. `.text` — corpo da resposta como **string** (decodificada).  
3. `open(..., "w", encoding="utf-8").write(...)` — salva o HTML em UTF‑8.  
4. `open(..., "r", encoding="utf-8").read()` — reabre e lê o arquivo para `arquivo_str`.

---

### Trecho 3 — Encontrar `<img alt="Palestrante">` e baixar imagens

```python
padrao_elemento_img = r'<\bimg\s.*?alt="Palestrante"\s.*?>'
elementos_img_match = re.findall(padrao_elemento_img, arquivo_str)

palestrantes = []

i = 0
for img in elementos_img_match:
    i += 1

    padrao_src = r'/\b.*?.png\b'
    src = re.search(padrao_src, img).group()

    padrao_nome_imagem = r"[\wÀ-ú\-\.]+(?=\.)"
    nome_imagem = re.search(padrao_nome_imagem, src).group()

    padrao_extensao = r"\.([\w]+)$"
    extensao = re.search(padrao_extensao, src).group(1)

    print(f"\n{i} {nome_imagem}.{extensao}")

    imagem = requests.get(url+src)
    nome_arquivo = f"{nome_imagem}.{extensao}"
    open(f"download\{nome_arquivo}", "wb").write(imagem.content)

    dict_palestrantes = {
        "image": nome_arquivo
    }
    palestrantes.append(dict_palestrantes)
```

**O que faz**  
Localiza as tags `<img ... alt="Palestrante" ...>`, extrai o caminho da imagem (`src` assumindo PNG), constrói o nome do arquivo e baixa/salva em `download/`. Inicia a lista `palestrantes` com a chave `image` preenchida.

**Passo a passo**  
1. `re.findall(...)` captura todas as tags de imagem de palestrantes.  
2. `re.search(padrao_src, img).group()` extrai o caminho relativo (`/...png`).  
3. `re.search(padrao_nome_imagem, src).group()` pega o nome base (antes do ponto).  
4. `re.search(padrao_extensao, src).group(1)` pega a extensão sem o ponto.  
5. `requests.get(url+src)` baixa os bytes da imagem.  
6. `open(..., "wb").write(imagem.content)` grava a imagem.  
7. `palestrantes.append({"image": nome_arquivo})` insere o registro inicial.

---

### Trecho 4 — Extrair nome e instituição

```python
padrao_nome_intituticao = r"<h4>.*?<\/h4>\s*<br>\s*<h6>.*?<\/h6>"
nomes_e_intituicoes = re.findall(padrao_nome_intituticao, arquivo_str)

i = 0
for nome_instituicao in nomes_e_intituicoes:
    padrao_nome = r"(?<=<h4>).*?(?=<\/h4>)"
    nome = re.search(padrao_nome, nome_instituicao).group()

    padrao_local_trabalho = r"(?<=<h6>).*?(?=<\/h6>)"
    local_trabalho = re.search(padrao_local_trabalho, nome_instituicao).group()

    palestrantes[i]["name"] = nome
    palestrantes[i]["work"] = local_trabalho

    i += 1
```

**O que faz**  
Encontra blocos `<h4>nome</h4><br><h6>instituição</h6>`, extrai `nome` e `local_trabalho` e completa os dicionários existentes em `palestrantes` nos índices correspondentes.

**Passo a passo**  
1. `re.findall` isola cada bloco nome+instituição.  
2. `re.search(...).group()` com *lookbehind/lookahead* extrai apenas o conteúdo interno de `<h4>` e `<h6>`.  
3. Atribui a `palestrantes[i]["name"]` e `["work"]` e incrementa `i`.

---

### Trecho 5 — Extrair e-mail

```python
padrao_email_sujo = r"<div.*?>\s*<p>.*?<\/p>\s*<\/div>"
emails_sujos = re.findall(padrao_email_sujo, arquivo_str)

i = 0
for email_sujo in emails_sujos:
    padrao_email = r"(?<=<p>).*?(?=<\/p>)"
    email = re.search(padrao_email, email_sujo).group()

    palestrantes[i]["email"] = email

    i += 1
```

**O que faz**  
Procura `<div> ... <p>email</p> ... </div>`, extrai o texto de `<p>` e preenche `email` em cada `palestrantes[i]`.

**Passo a passo**  
1. `re.findall` obtém os blocos.  
2. `re.search(...).group()` extrai o conteúdo da tag `<p>`.  
3. Atribui ao campo `"email"` e incrementa `i`.

---

### Trecho 6 — Persistir no SQLite

```python
conexao = sqlite3.connect('event.db')
cursor = conexao.cursor()

cursor.execute("DROP TABLE IF EXISTS speaker;")
conexao.commit() 

cursor.execute("""
    CREATE TABLE IF NOT EXISTS speaker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL,
        work VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        image VARCHAR(255) NOT NULL
    );
""")
conexao.commit()

for palestrante in palestrantes:
    cursor.execute('''
        INSERT INTO speaker (name, work, email, image)
        VALUES (?, ?, ?, ?);
    ''', (
        palestrante["name"],
        palestrante["work"],
        palestrante["email"],
        palestrante["image"]
    ))
conexao.commit() 
conexao.close()
```

**O que faz**  
Cria/abre `event.db`, (re)cria a tabela `speaker`, insere registros usando **parâmetros `?`** para segurança e fecha a conexão.

**Passo a passo**  
1. `sqlite3.connect`/`cursor` — abre o banco e cria um cursor.  
2. `DROP TABLE IF EXISTS` + `CREATE TABLE` — garante o esquema.  
3. `INSERT ... VALUES (?, ?, ?, ?)` — **binding** seguro dos valores.  
4. `commit()` — grava as mudanças; `close()` encerra.

---

## Esquema do Banco

Tabela `speaker`:
- `id` — chave primária (auto‑incremento)  
- `name` — nome do palestrante  
- `work` — instituição/local de trabalho  
- `email` — e‑mail do palestrante  
- `image` — nome do arquivo da imagem salva em `download/`

---
