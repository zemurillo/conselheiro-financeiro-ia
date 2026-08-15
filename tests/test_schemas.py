"""Testes unitários dos schemas base (AgentRole, AgentContext, AgentResponse).

CONCEITOS DE PYTEST USADOS NESTE ARQUIVO:

1. O pytest identifica testes por CONVENÇÃO DE NOME:
   - o arquivo precisa começar com `test_` (ou terminar em `_test.py`)
   - cada função de teste precisa começar com `test_`
   Não existe registro manual, decorator obrigatório nem lista de testes
   em outro lugar — o pytest varre o projeto procurando esse padrão.

2. Cada função `test_*` é INDEPENDENTE das outras. Elas não compartilham
   estado entre si (ao contrário das células do notebook, que rodam em
   sequência e podem depender do que veio antes).

3. `assert` é o coração de um teste: se a expressão depois do `assert`
   for `False`, o pytest marca aquele teste como FALHOU e mostra o que
   esperava vs. o que recebeu. Se for `True`, o teste passa em silêncio.

4. `pytest.raises(...)` é como você testa que um ERRO acontece de propósito
   -- por exemplo, "isso DEVE dar ValueError". Sem isso, você teria que
   usar try/except manualmente em todo teste de erro.

COMO RODAR:
    pytest tests/test_schemas.py -v
    (o -v é "verbose": mostra o nome de cada teste e se passou ou falhou)
"""

import pytest
from pydantic import ValidationError

from src.core.schemas import AgentContext, AgentResponse, AgentRole


# ---------------------------------------------------------------------------
# Testes de AgentRole
# ---------------------------------------------------------------------------


def test_agent_role_compara_como_string():
    """AgentRole herda de (str, Enum), então deve se comportar como string
    em comparações. Este teste documenta e trava esse comportamento: se um
    dia alguém remover o `str` da herança sem querer, esse teste quebra e
    avisa que algo mudou.
    """
    assert AgentRole.INVESTIMENTOS == "investimentos"


def test_agent_role_converte_string_valida():
    """Testa o "caminho feliz": converter uma string válida para o Enum.
    É o que vai acontecer, por exemplo, quando um valor vier de um JSON
    da API e precisar virar um AgentRole de verdade.
    """
    role = AgentRole("dividas")
    assert role == AgentRole.DIVIDAS


def test_agent_role_rejeita_string_invalida():
    """Testa o "caminho triste": uma string que NÃO é um valor válido do
    Enum deve dar erro, não passar silenciosamente. Isso é o que protege
    contra typos como "investimento" (faltando o 's') se infiltrarem sem
    ninguém perceber.

    `pytest.raises(ValueError)` funciona como um bloco `with`: o código
    DENTRO dele precisa lançar um ValueError, ou o teste falha (porque
    esperávamos o erro e ele não aconteceu).
    """
    with pytest.raises(ValueError):
        AgentRole("investimento")  # sem o 's' -- valor que não existe no Enum


# ---------------------------------------------------------------------------
# Testes de AgentContext
# ---------------------------------------------------------------------------


def test_agent_context_criacao_minima():
    """Testa que dá pra criar um AgentContext passando só os campos
    obrigatórios (session_id e user_message) -- os outros dois
    (history, metadata) devem vir preenchidos com valores padrão.
    """
    contexto = AgentContext(session_id="sessao-1", user_message="Olá")

    assert contexto.session_id == "sessao-1"
    assert contexto.user_message == "Olá"
    assert contexto.history == []
    assert contexto.metadata == {}


def test_agent_context_history_nao_e_compartilhado_entre_instancias():
    """Este teste existe por causa da pegadinha do Python que expliquei
    antes: se `history` fosse um valor padrão mutável mal configurado
    (tipo `history: list = []` direto, sem default_factory), todas as
    instâncias compartilhariam a MESMA lista na memória.

    Aqui criamos duas instâncias, modificamos o history de uma, e
    garantimos que a outra não foi afetada -- provando que
    `default_factory=list` está funcionando como esperado.
    """
    contexto_a = AgentContext(session_id="a", user_message="oi")
    contexto_b = AgentContext(session_id="b", user_message="oi")

    contexto_a.history.append({"role": "user", "content": "mensagem"})

    assert len(contexto_a.history) == 1
    assert len(contexto_b.history) == 0  # b não pode ter sido afetado


def test_agent_context_rejeita_tipo_errado():
    """Pydantic valida tipos automaticamente. Aqui garantimos que passar
    um número no lugar de uma string (`session_id`) é barrado com
    ValidationError -- é o Pydantic fazendo esse trabalho por nós, sem
    precisarmos escrever `if not isinstance(...)` manualmente em lugar
    nenhum do código.
    """
    with pytest.raises(ValidationError):
        AgentContext(session_id=123, user_message="teste")


# ---------------------------------------------------------------------------
# Testes de AgentResponse
# ---------------------------------------------------------------------------


def test_agent_response_valores_padrao():
    """Confirma os valores padrão de uma resposta: requires_review deve
    começar como False (só vira True quando um agente decide sinalizar
    algo pro guardrail), e created_at deve ser preenchido automaticamente
    (não precisamos passar a data manualmente).
    """
    resposta = AgentResponse(agent=AgentRole.INVESTIMENTOS, content="texto")

    assert resposta.requires_review is False
    assert resposta.created_at is not None


def test_agent_response_aceita_agent_role_como_string():
    """Pydantic é flexível o suficiente pra aceitar uma string crua no
    lugar de um AgentRole, desde que a string seja um valor válido do
    Enum -- ele converte automaticamente. Isso é útil quando a resposta
    vem de fora (ex: JSON da API) e ainda não foi convertida manualmente.
    """
    resposta = AgentResponse(agent="dividas", content="texto")

    assert resposta.agent == AgentRole.DIVIDAS
