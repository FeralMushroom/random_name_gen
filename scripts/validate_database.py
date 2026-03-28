"""
Walidacja baz adj_forms.json, noun_lemmas.json, dop_forms.json.

Sprawdza heurystycznie czy formy wyglądają poprawnie morfologicznie.
Wypisuje podejrzane wpisy do przejrzenia.
"""
import json
import os
import re
from collections import defaultdict

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def load(f):
    with open(os.path.join(DATA_DIR, f), encoding="utf-8") as fh:
        return json.load(fh)


# ── Heurystyki polskiej morfologii ───────────────────────────────────────────

ADJ_M_OK = re.compile(r"(y|i|ów)$")          # wielki, dobry, zły
ADJ_F_OK = re.compile(r"a$")                  # wielka, dobra
ADJ_N_OK = re.compile(r"(e|ie)$")             # wielkie, dobre

# Rzeczowniki — końcówki sugerujące rodzaj
NOUN_F_TYPICAL = re.compile(r"(a|ia|ość|nia|ja|ija|ea)$")
NOUN_N_TYPICAL = re.compile(r"(o|e|ę|um|ium|eum)$")

# Dopełniacz — typowe końcówki (bardzo szerokie)
DOP_OK = re.compile(r"(a|u|i|y|ów|iego|ej|ego|ię|ią)$")

# Podejrzane: cyfry, wielka litera, zbyt krótkie, zbyt długie, nie-polskie znaki
RE_DIGIT   = re.compile(r"\d")
RE_UPPER   = re.compile(r"[A-ZĄĆĘŁŃÓŚŹŻ]")
RE_FOREIGN = re.compile(r"[qvxQVX]")          # litery rzadkie w polskim
RE_SPACE   = re.compile(r"\s")


def flags(word):
    """Zwraca listę flag ostrzegawczych dla słowa."""
    f = []
    if RE_DIGIT.search(word):    f.append("cyfra")
    if RE_UPPER.match(word):     f.append("wielka_litera")
    if RE_FOREIGN.search(word):  f.append("obca_litera")
    if RE_SPACE.search(word):    f.append("spacja")
    if "-" in word:              f.append("myślnik")
    return f


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def show(items, limit=30):
    for item in items[:limit]:
        print(f"  {item}")
    if len(items) > limit:
        print(f"  ... i jeszcze {len(items)-limit} więcej")


# ════════════════════════════════════════════════════════════════
# PRZYMIOTNIKI
# ════════════════════════════════════════════════════════════════
def check_adj():
    section("PRZYMIOTNIKI  (adj_forms.json)")
    adj = load("adj_forms.json")
    print(f"Łącznie: {len(adj):,} tripletów")

    bad_m, bad_f, bad_n, flagged = [], [], [], []

    for triplet in adj:
        if len(triplet) != 3:
            flagged.append(f"zły rozmiar: {triplet}")
            continue
        m, f, n = triplet

        if not ADJ_M_OK.search(m): bad_m.append(f"{m} | {f} | {n}")
        if not ADJ_F_OK.search(f): bad_f.append(f"{m} | {f} | {n}")
        if not ADJ_N_OK.search(n): bad_n.append(f"{m} | {f} | {n}")

        for w in (m, f, n):
            fl = flags(w)
            if fl:
                flagged.append(f"{m} | {f} | {n}  [{', '.join(fl)}]")
                break

    print(f"\nForma MĘSKA nie pasuje do wzorca (*y/*i):  {len(bad_m):,}")
    show(bad_m)

    print(f"\nForma ŻEŃSKA nie pasuje do wzorca (*a):   {len(bad_f):,}")
    show(bad_f)

    print(f"\nForma NIJAKA nie pasuje do wzorca (*e/*ie): {len(bad_n):,}")
    show(bad_n)

    print(f"\nPodejrzane znaki / wielka litera:          {len(flagged):,}")
    show(flagged)


# ════════════════════════════════════════════════════════════════
# RZECZOWNIKI
# ════════════════════════════════════════════════════════════════
def check_nouns():
    section("RZECZOWNIKI  (noun_lemmas.json)")
    nouns = load("noun_lemmas.json")

    for gender, words in nouns.items():
        print(f"\nRodzaj [{gender}]: {len(words):,} słów")
        flagged = []
        wrong_gender = []

        for w in words:
            fl = flags(w)
            if fl:
                flagged.append(f"{w}  [{', '.join(fl)}]")

            # Podejrzane przypisanie rodzaju
            if gender == "m" and NOUN_F_TYPICAL.search(w) and not w.endswith("a") == False:
                # Rzeczownik kończący się na -a w rodzaju męskim — możliwe ale rzadkie
                if w.endswith("a") and not w.endswith("ista") and not w.endswith("ata") \
                        and not w.endswith("anta") and not w.endswith("enta"):
                    wrong_gender.append(f"{w}  [końcówka -a ale rodzaj m?]")
            elif gender == "n" and not NOUN_N_TYPICAL.search(w):
                wrong_gender.append(f"{w}  [rodzaj n ale końcówka nietypowa]")

        if flagged:
            print(f"  Podejrzane znaki: {len(flagged):,}")
            show(flagged)
        if wrong_gender:
            print(f"  Podejrzane przypisanie rodzaju: {len(wrong_gender):,}")
            show(wrong_gender, limit=20)
        if not flagged and not wrong_gender:
            print("  OK — brak oczywistych anomalii")


# ════════════════════════════════════════════════════════════════
# DOPEŁNIACZE
# ════════════════════════════════════════════════════════════════
def check_dop():
    section("DOPEŁNIACZE  (dop_forms.json)")
    dop = load("dop_forms.json")
    print(f"Łącznie: {len(dop):,} form")

    bad_ending = []
    flagged    = []
    nie_count  = sum(1 for d in dop if d.startswith("nie"))

    for d in dop:
        fl = flags(d)
        if fl:
            flagged.append(f"{d}  [{', '.join(fl)}]")
        elif not DOP_OK.search(d):
            bad_ending.append(d)

    print(f"Formy z przedrostkiem 'nie-': {nie_count:,}")
    print(f"\nKońcówka nie pasuje do typowego dopełniacza: {len(bad_ending):,}")
    show(bad_ending)
    print(f"\nPodejrzane znaki / wielka litera: {len(flagged):,}")
    show(flagged)


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    check_adj()
    check_nouns()
    check_dop()
    print("\n" + "="*60)
    print("  Gotowe.")
    print("="*60)
