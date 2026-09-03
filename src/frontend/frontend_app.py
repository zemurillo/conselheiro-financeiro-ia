"""Interface de chat em Streamlit, consumindo a API via HTTP.

Rodar localmente (com a API já rodando em outro terminal):
    streamlit run src/frontend/app.py

Repare que este arquivo NUNCA importa nada de `src.agents` ou
`src.core` -- ele só conhece a URL da API. Essa é a prova, na prática,
de que a camada de API está de fato desacoplando frontend de lógica de
negócio: se amanhã você trocar o LangGraph por outra coisa por trás da
API, este arquivo não muda uma linha.
"""

import uuid

import httpx
import streamlit as st

API_URL = "http://localhost:8000/chat"  # ajuste se sua API rodar em outro host/porta

st.set_page_config(page_title="Conselheiro Financeiro IA", page_icon="💰")
st.title("💰 Conselheiro Financeiro IA")
st.caption("Conteúdo educacional. Nunca recomendamos um investimento específico.")

# --- Estado da sessão do Streamlit ---
# O Streamlit RE-EXECUTA o script inteiro a cada interação do usuário
# (cada mensagem enviada, cada clique). Sem um lugar para "lembrar"
# coisas entre uma execução e outra, você perderia o histórico do chat
# a cada mensagem nova. `st.session_state` é exatamente esse lugar --
# um dicionário que sobrevive entre as re-execuções, enquanto a aba do
# navegador continuar aberta.
if "session_id" not in st.session_state:
    # Um id único por aba de navegador aberta. É isso que a API usa
    # (lembra do `_historicos` dict no main.py?) para saber de quem é
    # cada histórico de conversa -- sem isso, a API não teria como
    # distinguir sua pergunta da de outra pessoa usando o app ao mesmo
    # tempo.
    st.session_state.session_id = str(uuid.uuid4())

if "mensagens" not in st.session_state:
    # Esta lista é só para EXIBIÇÃO na tela -- o histórico "de verdade"
    # que alimenta o próximo agente vive na API (_historicos), não aqui.
    st.session_state.mensagens = []

# --- Renderiza as mensagens já trocadas nesta sessão ---
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Campo de entrada ---
# `st.chat_input` devolve None enquanto o usuário não enviar nada, e o
# texto digitado no momento em que ele aperta Enter/envia.
pergunta = st.chat_input("Digite sua pergunta sobre finanças...")

if pergunta:
    # 1. mostra a pergunta do usuário na tela imediatamente
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    # 2. chama a API e mostra a resposta
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                resposta_http = httpx.post(
                    API_URL,
                    json={
                        "session_id": st.session_state.session_id,
                        "message": pergunta,
                    },
                    timeout=30.0,
                )
                resposta_http.raise_for_status()  # levanta erro se a API devolver status 4xx/5xx
                dados = resposta_http.json()

                # TODO (seu turno): use os campos que a API já devolve
                # para enriquecer a exibição:
                #
                #   1. `dados["agent"]` -- mostre uma legenda acima da
                #      resposta, tipo:
                #          
                #      antes do st.markdown(texto_resposta) abaixo.
                #
                #   2. `dados["blocked"]` -- quando vier True (depois
                #      que você implementar o TODO do main.py da API),
                #      troque `st.markdown` por `st.warning` aqui, para
                #      deixar visualmente claro que aquela resposta foi
                #      recusada pelo guardrail, em vez de parecer uma
                #      resposta normal.

                texto_resposta = dados["content"]
                if dados["blocked"]:
                    st.warning(texto_resposta)
                else:
                    st.caption(f"🏦 respondido por: {dados['agent']}")
                    st.markdown(texto_resposta)

            except httpx.HTTPError as e:
                # Cobre tanto "API fora do ar" quanto "API devolveu
                # erro" -- nos dois casos, mostramos algo pro usuário
                # em vez de deixar o Streamlit quebrar sem explicação.
                texto_resposta = f"Não consegui falar com o servidor: {e}"
                st.error(texto_resposta)

    # 3. guarda a resposta no histórico de EXIBIÇÃO (não afeta o
    # histórico "de verdade" da conversa, que já foi atualizado dentro
    # da própria API)
    st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
