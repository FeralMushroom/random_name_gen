# Random Polish Phrase Generator

Generates random Polish phrases by combining adjectives, nouns, and genitive forms pulled from [PoliMorf](http://zil.ipipan.waw.pl/PoliMorf) — a large Polish morphological dictionary. Adjectives are matched to noun gender so the output is at least grammatically consistent, even if the meaning is complete nonsense.

Three frontends, one generator:
- **Desktop GUI** — tkinter app with TTS, phrase history, save to file
- **Discord bot** — per-server mode and safe/unsafe toggle, persists settings across restarts
- **Streamlit** — simple public web page

## How it works

PoliMorf is parsed once by `scripts/build_database.py` which extracts adjective triplets `[masculine, feminine, neuter]`, noun lemmas grouped by gender, and genitive singular forms. These get saved as JSON files. At runtime the generator just picks randomly from those lists and capitalizes.

Word quality is handled by `scripts/filter_database.py` — it filters out obscure/technical words using length limits and [wordfreq](https://github.com/rspeer/wordfreq) frequency data for Polish. Originals are backed up to `data/backup/` so you can always re-run with different thresholds.

Offensive words are tracked separately in `data/unsafe.json`. Safe mode (on by default) excludes them at load time.

## Setup

Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

For the first run you also need to download PoliMorf and build the databases:

```bash
python scripts/setup.py          # downloads PoliMorf.tab.gz
python scripts/build_database.py # parses it, writes data/*.json
python scripts/filter_database.py # filters by quality
```

This only needs to be done once. After that `data/*.json` is everything the generator needs.

## Running

**GUI**
```bash
python rgen.py
```

**Discord bot** — put your token in `random_name_gen.env`:
```
DISCORD_TOKEN=your_token_here
```
Then either:
```bash
python bot.py          # in terminal
```
or double-click `run_bot.pyw` for a small launcher window.

**Streamlit**
```bash
streamlit run streamlit_app.py
```

## Bot commands

| Command | Description |
|---|---|
| `.random [n]` | generate n phrases (default 1) |
| `.prd` | set mode: adjective + noun + genitive |
| `.pr` | set mode: adjective + noun |
| `.rd` | set mode: noun + genitive |
| `.safe` / `.unsafe` | toggle content filter |
| `.status` | show current settings |
| `.help` | show all commands |

## Project structure

```
generator.py        — core logic, imported by everything else
rgen.py             — desktop GUI
bot.py              — Discord bot
run_bot.pyw         — bot launcher window (no console)
streamlit_app.py    — web UI

scripts/
  setup.py          — downloads PoliMorf
  build_database.py — parses PoliMorf into JSON
  filter_database.py — filters word lists by quality
  tag_words.py      — CLI tool for tagging unsafe words
  validate_database.py — sanity checks on word lists

data/
  adj_forms.json    — adjective triplets [m, f, n]
  noun_lemmas.json  — nouns by gender
  dop_forms.json    — genitive forms
  custom_dop.json   — genitive forms not in PoliMorf (preserved from original list)
  unsafe.json       — flagged words excluded in safe mode
```
