"""Configuração do pytest para todo o projeto.

Este arquivo, mesmo vazio de testes, tem um efeito importante: sua
simples PRESENÇA na raiz do projeto faz o pytest adicionar essa pasta
ao sys.path antes de coletar os testes.

Por que isso era necessário: os arquivos dentro de `tests/` fazem
`from src.agents.base import BaseAgent` etc. Sem este conftest.py, o
pytest só conhece a pasta `tests/` (onde não existe pacote `src`), e
não a raiz do projeto (onde `src/` de fato está) -- daí o erro
`ModuleNotFoundError: No module named 'src'`.

Não é necessário escrever nada aqui para este projeto funcionar; o
arquivo existir já resolve o problema de import.
"""
