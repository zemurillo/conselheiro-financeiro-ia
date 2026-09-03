"""Configuração da conexão com o banco de dados (SQLAlchemy)."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# DATABASE_URL vem do seu .env (ex.: sqlite:///./data/app.db). Se não
# estiver definida, cai num SQLite local por padrão -- assim o projeto
# funciona mesmo sem configurar nada extra.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/app.db")

# `connect_args` com `check_same_thread=False` é uma particularidade do
# SQLite: por padrão, ele só permite que a MESMA thread que abriu a
# conexão a utilize. Como o FastAPI pode atender requisições em
# threads diferentes, isso quebraria sem essa flag. Não é necessário
# para Postgres/MySQL -- é só peculiaridade do SQLite.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

# `sessionmaker` é uma FÁBRICA de sessões de banco -- cada vez que você
# chama `SessionLocal()`, ganha uma sessão nova e independente, que
# sabe conversar com o `engine` configurado acima. Isso é o mesmo
# padrão de injeção de dependência que você já viu nos agentes, só que
# aqui é o próprio FastAPI que vai chamar essa fábrica (veja `get_db`).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# `Base` é a classe da qual todo MODELO (tabela) do projeto herda. É o
# que permite ao SQLAlchemy reconhecer quais classes Python representam
# tabelas, e gerar o SQL de criação delas automaticamente.
Base = declarative_base()


def get_db():
    """Fornece uma sessão de banco de dados, uma por requisição.

    Este é o padrão de "dependency" do FastAPI: você declara
    `db: Session = Depends(get_db)` num endpoint, o FastAPI chama esta
    função pra você, entrega o que vier do `yield`, e garante que
    `db.close()` roda no final -- mesmo se a requisição der erro no
    meio do caminho. É a forma idiomática de garantir que toda conexão
    aberta também é fechada, sem você ter que lembrar de fazer isso
    manualmente em cada endpoint.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Cria as tabelas no banco, se ainda não existirem.

    `Base.metadata.create_all` olha para todos os modelos que herdam de
    `Base` (definidos em models.py) e executa o equivalente a um
    `CREATE TABLE IF NOT EXISTS` para cada um. Chamamos isso uma vez,
    quando a API sobe (veja o `@app.on_event("startup")` no main.py).
    """
    # Garante que a pasta `data/` existe antes do SQLite tentar criar
    # o arquivo .db dentro dela -- sem isso, a primeira execução falha
    # se a pasta não existir ainda.
    if DATABASE_URL.startswith("sqlite:///"):
        caminho_arquivo = DATABASE_URL.replace("sqlite:///", "")
        pasta = os.path.dirname(caminho_arquivo)
        if pasta:
            os.makedirs(pasta, exist_ok=True)

    Base.metadata.create_all(bind=engine)
