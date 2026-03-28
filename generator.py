"""
Główna logika generowania fraz.
Importowana przez GUI (rgen.py), Discord bota i Streamlit.
"""
import random
import json
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))

def _load(filename):
    with open(os.path.join(_ROOT, "data", filename), encoding="utf-8") as f:
        return json.load(f)


_all_adj  = _load("adj_forms.json")   # [[m, f, n], ...]
_all_noun = _load("noun_lemmas.json") # {"m": [...], "f": [...], "n": [...]}

# Dopełniacze z dwóch źródeł: PoliMorf + słowa z custom_dop.json których nie ma w PoliMorfie
_dop_polimorf    = _load("dop_forms.json")
_custom_dop_path = os.path.join(_ROOT, "data", "custom_dop.json")
_custom_dop      = json.load(open(_custom_dop_path, encoding="utf-8")) \
                   if os.path.exists(_custom_dop_path) else []
_dop_set  = {w.lower() for w in _dop_polimorf}  # custom ma wielkie litery — porównanie case-insensitive
_all_dop  = _dop_polimorf + [w for w in _custom_dop if w.lower() not in _dop_set]

_adj_nie    = [f for f in _all_adj if f[0].startswith("nie")]
_adj_normal = [f for f in _all_adj if not f[0].startswith("nie")]
_dop_nie    = [d for d in _all_dop if d.startswith("nie")]
_dop_normal = [d for d in _all_dop if not d.startswith("nie")]

_unsafe_path = os.path.join(_ROOT, "data", "unsafe.json")
if os.path.exists(_unsafe_path):
    _u           = _load("unsafe.json")
    _unsafe_adj  = set(_u.get("adj",  []))
    _unsafe_noun = set(_u.get("noun", []))
    _unsafe_dop  = {w.lower() for w in _u.get("dop", [])}
else:
    _unsafe_adj  = set()
    _unsafe_noun = set()
    _unsafe_dop  = set()

_safe_adj_nie    = [f for f in _adj_nie    if f[0] not in _unsafe_adj]
_safe_adj_normal = [f for f in _adj_normal if f[0] not in _unsafe_adj]
_safe_noun       = {g: [n for n in nouns if n not in _unsafe_noun]
                    for g, nouns in _all_noun.items()}
_safe_dop_nie    = [d for d in _dop_nie    if d.lower() not in _unsafe_dop]
_safe_dop_normal = [d for d in _dop_normal if d.lower() not in _unsafe_dop]

_GENDER_IDX = {"m": 0, "f": 1, "n": 2}
MODES = ["adj+n+gen", "adj+n", "n+gen"]


def generate_phrase(mode: str = "adj+n+gen", safe: bool = True) -> str:
    """
    Generuje losową frazę.

    mode:
      "adj+n+gen" — Przymiotnik Rzeczownik Dopełniacz  (domyślny)
      "adj+n"     — Przymiotnik Rzeczownik
      "n+gen"     — Rzeczownik Dopełniacz

    safe:
      True  — filtruje słowa z unsafe.json  (domyślny)
      False — pełna baza, bez filtrowania
    """
    adj_nie    = _safe_adj_nie    if safe else _adj_nie
    adj_normal = _safe_adj_normal if safe else _adj_normal
    noun_pool  = _safe_noun       if safe else _all_noun
    dop_nie    = _safe_dop_nie    if safe else _dop_nie
    dop_normal = _safe_dop_normal if safe else _dop_normal

    gender = random.choice(["m", "f", "n"])
    noun   = random.choice(noun_pool[gender]).capitalize()

    def pick_dop() -> str:
        # "nie-" formy mają wagę 1:9 żeby nie dominowały outputu
        pool = dop_normal if (random.random() < 0.9 and dop_normal) else dop_nie
        return random.choice(pool).capitalize()

    if mode in ("adj+n+gen", "adj+n"):
        # "nie-" formy mają wagę 1:9 żeby nie dominowały outputu
        pool  = adj_normal if (random.random() < 0.9 and adj_normal) else adj_nie
        forms = random.choice(pool)
        adj   = forms[_GENDER_IDX[gender]].capitalize()
        if mode == "adj+n+gen":
            return f"{adj} {noun} {pick_dop()}"
        return f"{adj} {noun}"

    if mode == "n+gen":
        return f"{noun} {pick_dop()}"

    return noun


_gui_safe = True

def set_safe_mode(enabled: bool):
    """Ustawia tryb safe dla GUI. Bot używa parametru safe= bezpośrednio."""
    global _gui_safe
    _gui_safe = enabled

def generate_phrase_gui(mode: str = "adj+n+gen") -> str:
    """Wersja dla GUI — respektuje set_safe_mode()."""
    return generate_phrase(mode=mode, safe=_gui_safe)


if __name__ == "__main__":
    try:
        ile = int(input("Ile fraz? "))
        for _ in range(ile):
            print(generate_phrase())
    except ValueError:
        print("Błąd: wpisz liczbę.")
