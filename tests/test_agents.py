"""Testes unitários de BaseAgent e AgenteInvestimentos.

CONCEITOS NOVOS NESTE ARQUIVO (além dos vistos em test_schemas.py):

1. FIXTURE (`@pytest.fixture`):
   É uma função que PREPARA algo que vários testes vão precisar, evitando
   repetir o mesmo setup em cada função de teste. Qualquer teste que
   declare um parâmetro com o MESMO NOME da fixture recebe automaticamente
   o que ela retornou -- o pytest resolve essa "injeção" sozinho, você
   não chama a fixture diretamente.

   Isso é o formalismo em cima do que você já fez no notebook manualmente
   (criar o objeto "espião"/falso uma vez e reusar em várias células).

2. MOCK / FAKE OBJECT:
   Em vez de usar um ChatOpenAI de verdade (que custaria dinheiro e
   dependeria de internet a cada teste), criamos uma classe falsa que
   IMITA a interface que o BaseAgent espera (um método `.invoke()` que
   devolve algo com `.content`). O agente não sabe a diferença -- é
   exatamente o benefício da injeção de dependência que vimos antes.

3. Testar um caso de ERRO em código abstrato:
   Testamos que `BaseAgent` não pode ser instanciada diretamente --
   isso prova que a trava do `@abstractmethod` está funcionando, e
   documenta essa regra pra quem ler os testes no futuro.

COMO RODAR:
    pytest tests/test_agents.py -v
"""

import pytest

from src.agents.base import BaseAgent
from src.agents.guardrails import AgentGuardrails
from src.agents.investimentos import AgenteInvestimentos
from src.core.schemas import AgentContext, AgentRole, GuardrailDecision


# ---------------------------------------------------------------------------
# "Dublês" (test doubles) -- substitutos falsos do LLM real, só para teste
# ---------------------------------------------------------------------------


class _RespostaFalsa:
    """Imita o objeto que um ChatModel real devolve: só precisa ter um
    atributo `.content`, que é tudo que o `AgenteInvestimentos.run()` lê
    do resultado do LLM.
    """

    def __init__(self, content: str) -> None:
        self.content = content


class _LLMFalso:
    """Substitui um LLM real nos testes.

    Guarda as mensagens recebidas em `self.mensagens_recebidas` -- isso
    permite que um teste depois verifique O QUE foi enviado ao "LLM" sem
    de fato chamar nenhuma API. É assim que testamos, por exemplo, que o
    system_prompt correto foi incluído na conversa.
    """

    def __init__(self, resposta: str = "resposta padrão de teste") -> None:
        self._resposta = resposta
        self.mensagens_recebidas: list[dict[str, str]] | None = None

    def invoke(self, messages: list[dict[str, str]]) -> _RespostaFalsa:
        self.mensagens_recebidas = messages
        return _RespostaFalsa(self._resposta)


class _LLMGuardrailFalso:
    def __init__(self, decisao: GuardrailDecision) -> None:
        self.decisao = decisao
        self.mensagens_recebidas = None

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        self.mensagens_recebidas = messages
        return self.decisao


# ---------------------------------------------------------------------------
# Fixtures -- setup reutilizável entre os testes deste arquivo
# ---------------------------------------------------------------------------


@pytest.fixture
def llm_falso() -> _LLMFalso:
    """Toda função de teste que declarar um parâmetro chamado `llm_falso`
    recebe uma instância NOVA disso -- o pytest cuida de chamar essa
    fixture antes de cada teste que precisar dela. "Nova" é importante:
    cada teste começa com um LLM falso limpo, sem "memória" do teste
    anterior.
    """
    return _LLMFalso(resposta="Tesouro Direto é uma plataforma pública de investimento.")


@pytest.fixture
def contexto_exemplo() -> AgentContext:
    """Um AgentContext pronto pra usar, pra não repetir a criação em
    cada teste que precisa de um contexto válido.
    """
    return AgentContext(
        session_id="sessao-teste",
        user_message="O que é tesouro direto?",
    )


# ---------------------------------------------------------------------------
# Testes de BaseAgent
# ---------------------------------------------------------------------------


def test_base_agent_nao_pode_ser_instanciada_diretamente():
    """BaseAgent é abstrata (ABC + @abstractmethod em run()). Tentar
    criar uma instância dela diretamente deve dar TypeError -- é o
    Python recusando porque a classe tem um método abstrato sem
    implementação. Esse teste prova, de forma automatizada, que essa
    trava de design continua funcionando (se algum dia alguém remover
    o @abstractmethod sem querer, este teste passa a falhar e avisa).
    """
    with pytest.raises(TypeError):
        BaseAgent(llm=None)


# ---------------------------------------------------------------------------
# Testes de AgenteInvestimentos
# ---------------------------------------------------------------------------


def test_agente_investimentos_usa_o_role_correto(llm_falso, contexto_exemplo):
    """Confirma que toda resposta do AgenteInvestimentos vem marcada com
    AgentRole.INVESTIMENTOS -- é o que permite ao orquestrador/frontend
    saber qual agente respondeu, sem inspecionar o conteúdo do texto.

    Repare que `llm_falso` e `contexto_exemplo` aparecem aqui como
    PARÂMETROS da função -- não estamos chamando as fixtures, o pytest
    as executa e passa o resultado automaticamente porque os nomes
    batem com as fixtures definidas acima.
    """
    agente = AgenteInvestimentos(llm=llm_falso)

    resposta = agente.run(contexto_exemplo)

    assert resposta.agent == AgentRole.INVESTIMENTOS


def test_agente_investimentos_retorna_o_conteudo_do_llm(llm_falso, contexto_exemplo):
    """Confirma que o texto que o "LLM" devolveu chega intacto até o
    AgentResponse final -- ou seja, que o `run()` não perde nem
    modifica o conteúdo no caminho.
    """
    agente = AgenteInvestimentos(llm=llm_falso)

    resposta = agente.run(contexto_exemplo)

    assert resposta.content == "Tesouro Direto é uma plataforma pública de investimento."


def test_agente_investimentos_inclui_system_prompt_na_chamada(llm_falso, contexto_exemplo):
    """Este é o teste mais importante deste arquivo: ele prova, de forma
    automatizada, o que fizemos manualmente com o "LLM espião" na
    conversa -- que o system_prompt REALMENTE é enviado ao LLM dentro
    da lista de mensagens.

    Usamos `llm_falso.mensagens_recebidas` (preenchido dentro do
    `.invoke()` do _LLMFalso) para inspecionar exatamente o que chegou
    até o "LLM", sem precisar chamar nenhuma API de verdade.
    """
    agente = AgenteInvestimentos(llm=llm_falso)

    agente.run(contexto_exemplo)

    mensagens = llm_falso.mensagens_recebidas
    assert mensagens is not None
    assert mensagens[0]["role"] == "system"
    assert mensagens[0]["content"] == agente.system_prompt


def test_agente_investimentos_inclui_pergunta_do_usuario_na_chamada(
    llm_falso, contexto_exemplo
):
    """Confirma que a pergunta do usuário (context.user_message) também
    chega na lista de mensagens, como a última entrada com role="user".
    """
    agente = AgenteInvestimentos(llm=llm_falso)

    agente.run(contexto_exemplo)

    ultima_mensagem = llm_falso.mensagens_recebidas[-1]
    assert ultima_mensagem["role"] == "user"
    assert ultima_mensagem["content"] == "O que é tesouro direto?"


def test_agente_investimentos_inclui_historico_da_conversa(llm_falso):
    """Diferente dos testes acima (que usam a fixture `contexto_exemplo`,
    sem histórico), aqui criamos um AgentContext MANUALMENTE com
    histórico prévio, pra confirmar que ele também entra na lista de
    mensagens -- entre o system prompt e a pergunta atual.
    """
    contexto_com_historico = AgentContext(
        session_id="sessao-teste",
        user_message="E fundos imobiliários?",
        history=[
            {"role": "user", "content": "O que é tesouro direto?"},
            {"role": "assistant", "content": "É uma plataforma pública."},
        ],
    )
    agente = AgenteInvestimentos(llm=llm_falso)

    agente.run(contexto_com_historico)

    mensagens = llm_falso.mensagens_recebidas
    # esperado: [system, history[0], history[1], user_message_atual] = 4 mensagens
    assert len(mensagens) == 4
    assert mensagens[1]["content"] == "O que é tesouro direto?"
    assert mensagens[2]["content"] == "É uma plataforma pública."


def test_guardrails_aprova_e_devolve_resposta_segura(contexto_exemplo):
    llm = _LLMGuardrailFalso(
        GuardrailDecision(approved=True, safe_response="Explicação educativa.")
    )

    resposta = AgentGuardrails(llm).run(contexto_exemplo)

    assert resposta.approved is True
    assert resposta.requires_review is False
    assert resposta.content == "Explicação educativa."


def test_guardrails_bloqueia_resposta_rejeitada(contexto_exemplo):
    llm = _LLMGuardrailFalso(
        GuardrailDecision(
            approved=False,
            reason="Recomendação de ativo específico.",
            safe_response="Não deve ser liberada.",
        )
    )

    resposta = AgentGuardrails(llm).run(contexto_exemplo)

    assert resposta.approved is False
    assert resposta.requires_review is True
    assert resposta.content == ""
    assert resposta.metadata["reason"] == "Recomendação de ativo específico."
