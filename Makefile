.RECIPEPREFIX := >

install:
>python -m venv .venv
>.venv/bin/pip install -r requirements.txt

db-up:
>docker compose up -d

test:
>pytest -q

extract-local:
>python -m src.main --sources file bigdata

extract-all:
>python -m src.main --sources all --continue-on-error
