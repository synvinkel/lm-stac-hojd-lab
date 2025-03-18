# LM HOJD

Download assets from the LM HOJD API.

Uses `UV`: https://docs.astral.sh/uv/getting-started/installation/#homebrew

## Usage

To set up credentials copy `.env.example` to `.env`:
```sh
cp .env.example .env
```

Edit `.env` to provide your credentials. These will automatically be loaded by the script when it runs.

Run script to download assets:
```sh
uv run lm_hojd.py
```

Run jupyter notebook:
```sh
uv run ipython kernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name=project
uv run --with jupyter jupyter lab
```
