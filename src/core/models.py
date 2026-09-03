"""Modelos ORM (tabelas do banco) -- diferente dos schemas Pydantic.

IMPORTANTE: estas classes representam TABELAS no banco de dados, não o
formato de entrada/saída da API, nem o AgentContext/AgentResponse dos
agentes. Repare que agora existem TRÊS camadas de "schema" diferentes
no projeto, cada uma com seu próprio motivo de existir:

  1. Pydantic em src/core/schemas.py e src/api/schemas.py -- validação
     e contrato de dados em memória / HTTP.
  2. SQLAlchemy aqui neste arquivo -- estrutura das tabelas no banco.

Nenhuma delas deveria "vazar" pra fora do seu contexto -- é o
repository.py (próximo arquivo) que faz a ponte entre elas, convertendo
linhas do banco em dicionários simples que o resto do código já
entende.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.core.database import Base


class SessaoDB(Base):
    """Uma conversa (uma sessão do Streamlit) registrada no banco."""

    __tablename__ = "sessoes"

    # `primary_key=True` marca esta coluna como identificador único da
    # linha -- toda tabela precisa de uma. Usamos o próprio session_id
    # (o uuid gerado pelo Streamlit) como chave primária, em vez de um
    # número autoincremental -- assim não precisamos de uma tabela de
    # "de-para" entre o uuid e um id interno.
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # `relationship` NÃO cria uma coluna no banco -- é um atalho do
    # SQLAlchemy pra você navegar de uma SessaoDB para todas as
    # MensagemDB associadas a ela (`sessao.mensagens`), sem escrever o
    # JOIN na mão toda vez.
    mensagens = relationship(
        "MensagemDB", back_populates="sessao", order_by="MensagemDB.id"
    )


class MensagemDB(Base):
    """Uma mensagem (do usuário ou de um agente) dentro de uma sessão."""

    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # `ForeignKey` diz ao banco: todo valor desta coluna precisa
    # existir como `id` na tabela `sessoes`. É o que impede, no nível
    # do próprio banco, que uma mensagem fique "órfã" -- associada a
    # uma sessão que não existe.
    session_id = Column(String, ForeignKey("sessoes.id"), nullable=False)

    role = Column(String, nullable=False)  # "user" ou "assistant"
    content = Column(Text, nullable=False)
    # qual AgentRole respondeu -- só preenchido quando role="assistant"
    agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sessao = relationship("SessaoDB", back_populates="mensagens")
