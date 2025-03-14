# LM HOJD

Download assets from the LM HOJD API.

Uses `UV`: https://docs.astral.sh/uv/getting-started/installation/#homebrew

## Usage

Run script to download assets:
```sh
uv run lm_hojd.py
```

Run jupyter notebook:
```sh
uv run ipython kernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name=project
uv run --with jupyter jupyter lab
```
