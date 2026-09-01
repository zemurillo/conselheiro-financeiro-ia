"""Fábrica de LLMs: decide, a partir do `.env`, qual provedor instanciar.

Isso é a mesma injeção de dependência que você já viu nos agentes, só
que aplicada um nível acima: em vez de cada agente/endpoint decidir
"qual LLM eu uso", centralizamos essa decisão aqui, num lugar só.
Trocar de provedor no futuro (ou usar um mais barato em produção)
significa mexer só neste arquivo -- nenhum agente muda.
"""

import os

from langchain_core.language_models import BaseChatModel


def get_llm() -> BaseChatModel:
    """Lê LLM_PROVIDER do ambiente e devolve o ChatModel correspondente.

    Valores esperados de LLM_PROVIDER (defina no seu `.env`):
    "openai", "anthropic" ou "groq". Se a variável não existir, assume
    "openai" como padrão -- já que é o provedor que você decidiu usar
    primeiro.
    """
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    # LLM_MODEL é opcional -- se não vier preenchido, cada branch abaixo
    # usa um modelo padrão razoável.
    model_name = os.environ.get("LLM_MODEL")

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model_name or "gpt-4o-mini", temperature=0.3)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model_name or "claude-sonnet-4-5", temperature=0.3)

    if provider == "groq":
        # TODO (seu turno): implemente este branch seguindo exatamente
        # o mesmo padrão dos dois acima:
        #   1. importe ChatGroq de langchain_groq (import LOCAL, dentro
        #      do if -- é assim que os outros dois fazem, para não
        #      obrigar quem só usa OpenAI a ter langchain-groq instalado
        #      funcionando perfeitamente)
        #   2. devolva `ChatGroq(model=model_name or "algum-modelo-padrao", ...)`
        #   3. escolha um modelo padrão da Groq (pesquise os disponíveis
        #      em console.groq.com -- ex.: "llama-3.3-70b-versatile")
        #   4. não esqueça de preencher GROQ_API_KEY no seu .env quando
        #      for testar esse provedor
        raise NotImplementedError(
            "Implemente o branch do Groq seguindo o padrão dos blocos acima."
        )

    raise ValueError(f"Provedor de LLM desconhecido: {provider!r}")
