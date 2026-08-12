# Dependências

Tratando-se de um pacote com as dependência gerenciadas pelo [uv](https://docs.astral.sh/uv/), para criar o ambiente de desenvolvimento basta dar o comando abaixo.

```shell
# Define a versão do python
uv python pin 3.11

# 
uv lock --upgrade

# Instala os pacotes definidos no pyproject.toml
uv sync --group docs --group dev
uv sync --group docs

# Ativa environment
.venv\Scripts\activate # Windows
source .venv/bin/activate # Linux
```

<br>

---

## Documentação

A documentação do projeto foi feita usando o [MkDocs](https://www.mkdocs.org/), com _deploy_ no [Read The Docs](https://app.readthedocs.org/).

Para testar localmente, basta usar:

```shell
# Serve Localmente
mkdocs serve --livereload
python -m mkdocs serve --livereload
```
