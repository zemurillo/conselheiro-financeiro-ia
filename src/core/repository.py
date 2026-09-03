"""Camada de acesso a dados -- isola o resto do código dos detalhes do SQLAlchemy.

Por que essa camada extra, em vez da API mexer direto com
`SessaoDB`/`MensagemDB`?

Mesma lógica de separação que você já viu entre `AgentContext` e
`ChatRequest`: se amanhã você trocar SQLite por Postgres, ou até trocar
SQLAlchemy por outra biblioteca, só ESTE arquivo muda -- o `main.py` da
API continua chamando `obter_historico(db, session_id)` exatamente do
mesmo jeito, sem saber (nem precisar saber) o que mudou por baixo.
"""

from sqlalchemy.orm import Session

from src.core.models import MensagemDB, SessaoDB


def obter_ou_criar_sessao(db: Session, session_id: str) -> SessaoDB:
    """Busca a sessão pelo id; cria uma linha nova se ainda não existir.

    `db.get(Modelo, chave_primaria)` é a forma do SQLAlchemy de buscar
    por chave primária -- equivale a um `SELECT ... WHERE id = ...`
    que devolve no máximo uma linha.
    """
    sessao = db.get(SessaoDB, session_id)
    if sessao is None:
        sessao = SessaoDB(id=session_id)
        db.add(sessao)  # marca o objeto para ser inserido na próxima escrita
        db.commit()  # de fato grava a transação no banco
        db.refresh(sessao)  # recarrega valores gerados pelo banco (ex.: created_at)
    return sessao


def obter_historico(db: Session, session_id: str) -> list[dict[str, str]]:
    """Devolve o histórico de uma sessão no MESMO FORMATO que
    `AgentContext.history` já espera -- uma lista de
    `{"role": ..., "content": ...}` -- para que o resto do código (o
    grafo) não precise saber que os dados vieram de um banco.
    """
    sessao = db.get(SessaoDB, session_id)
    if sessao is None:
        return []
    return [{"role": m.role, "content": m.content} for m in sessao.mensagens]


def salvar_mensagem(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    agent: str | None = None,
) -> MensagemDB:
    """Grava uma mensagem nova associada a uma sessão.

    Chama `obter_ou_criar_sessao` primeiro -- necessário porque a
    ForeignKey em MensagemDB exige que a sessão já exista antes de
    qualquer mensagem apontar para ela.
    """
    obter_ou_criar_sessao(db, session_id)

    mensagem = MensagemDB(session_id=session_id, role=role, content=content, agent=agent)
    db.add(mensagem)
    db.commit()
    db.refresh(mensagem)
    return mensagem


# TODO (seu turno): implemente `contar_mensagens(db, session_id) -> int`,
# devolvendo quantas mensagens existem numa sessão. Isso é útil, por
# exemplo, pra limitar o tamanho do histórico enviado ao LLM (evitar
# mandar uma conversa de 500 mensagens pro modelo a cada pergunta nova
# -- o que custaria caro e estouraria o limite de contexto).
#
# Duas formas de implementar, da mais simples à mais eficiente:
#   1. `return len(obter_historico(db, session_id))` -- reaproveita o
#      que já existe, mas carrega TODAS as mensagens na memória só
#      pra contar.
#   2. `return db.query(MensagemDB).filter(MensagemDB.session_id == session_id).count()`
#      -- pede pro banco fazer a contagem, sem trazer nenhuma linha
#      pra memória. Prefira esta em sessões que podem ficar grandes.
