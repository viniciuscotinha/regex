import requests
import re
import sqlite3

url = "https://eventos.ifgoiano.edu.br"
codigo_fonte = requests.get(f"{url}/integra2025/")
codigo_fonte_string = codigo_fonte.text

open("codigo_fonte.txt", "w", encoding='utf-8').write(codigo_fonte_string)

arquivo_str = open("codigo_fonte.txt","r", encoding='utf-8').read()

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

padrao_email_sujo = r"<div.*?>\s*<p>.*?</p>\s*</div>"
emails_sujos = re.findall(padrao_email_sujo, arquivo_str)

i = 0
for email_sujo in emails_sujos:
    padrao_email = r"(?<=<p>).*?(?=<\/p>)"
    email = re.search(padrao_email, email_sujo).group()

    palestrantes[i]["email"] = email

    i += 1

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