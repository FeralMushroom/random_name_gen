"""
Krok 2: przetwarza PoliMorf.tab.gz i zapisuje:
  data/adj_forms.json    — lista [m_forma, f_forma, n_forma] dla każdego przymiotnika
  data/noun_lemmas.json  — rzeczowniki pogrupowane wg rodzaju {m, f, n}
  data/dop_forms.json    — formy dopełniacza lp. rzeczowników

Uruchom po setup.py, z dowolnego miejsca.
"""
import gzip
import json
import os
from collections import defaultdict

PROJECT_ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLIMORF_PATH = os.path.join(PROJECT_ROOT, "PoliMorf.tab.gz")
OUTPUT_ADJ    = os.path.join(PROJECT_ROOT, "data", "adj_forms.json")
OUTPUT_NOUN   = os.path.join(PROJECT_ROOT, "data", "noun_lemmas.json")
OUTPUT_DOP    = os.path.join(PROJECT_ROOT, "data", "dop_forms.json")

# Format PoliMorf: form \t lemma \t tag \t typ
# tag używa kropek dla wielu wartości: adj:sg:nom.voc:m1.m2.m3:pos


def build():
    if not os.path.exists(POLIMORF_PATH):
        print(f"Błąd: nie znaleziono {POLIMORF_PATH}")
        print("Najpierw uruchom: python scripts/setup.py")
        return

    adj_forms   = defaultdict(dict)  # {lemma: {"m": form, "f": form, "n": form}}
    noun_lemmas = defaultdict(set)   # {"m"/"f"/"n": {lemmat, ...}}
    dop_forms   = set()

    print("Przetwarzanie PoliMorf (może chwilę potrwać)...")
    line_count = 0

    with gzip.open(POLIMORF_PATH, "rt", encoding="utf-8") as f:
        for line in f:
            line_count += 1
            if line_count % 500_000 == 0:
                print(f"  {line_count:,} linii...")

            parts = line.strip().split("\t")
            if len(parts) < 3:
                continue

            form, lemma, tag = parts[0], parts[1], parts[2]
            word_type = parts[3] if len(parts) >= 4 else "pospolita"

            if word_type == "własna":
                continue

            tag_parts = tag.split(":")
            if len(tag_parts) < 4:
                continue

            pos, number, case_field, gender_field = tag_parts[0], tag_parts[1], tag_parts[2], tag_parts[3]
            genders = gender_field.split(".")

            # Dopełniacze zbieramy niezależnie od pozostałych filtrów
            if pos == "subst" and number == "sg" and "gen" in case_field.split("."):
                if not lemma[0].isupper() and len(form) > 3:
                    dop_forms.add(form)

            # Dalej interesuje nas tylko mianownik lp.
            if number != "sg" or "nom" not in case_field.split("."):
                continue

            if pos == "adj":
                if lemma[0].isupper():
                    continue
                # m1/m2/m3 = rodzaje męskie
                if any(g in genders for g in ("m1", "m2", "m3")):
                    if "m" not in adj_forms[lemma]:
                        adj_forms[lemma]["m"] = form
                elif "f" in genders:
                    if "f" not in adj_forms[lemma]:
                        adj_forms[lemma]["f"] = form
                elif any(g.startswith("n") for g in genders):
                    if "n" not in adj_forms[lemma]:
                        adj_forms[lemma]["n"] = form

            elif pos == "subst" and form == lemma:
                if lemma[0].isupper() or len(lemma) <= 3:
                    continue
                if any(g in genders for g in ("m1", "m2", "m3")):
                    noun_lemmas["m"].add(lemma)
                elif "f" in genders:
                    noun_lemmas["f"].add(lemma)
                elif any(g.startswith("n") for g in genders):
                    noun_lemmas["n"].add(lemma)

    # Tylko przymiotniki z kompletnymi formami m + f + n
    complete = [
        [v["m"], v["f"], v["n"]]
        for v in adj_forms.values()
        if "m" in v and "f" in v and "n" in v
    ]

    print(f"\nWyniki:")
    print(f"  Przymiotniki (kompletne tripletki m/f/n): {len(complete):,}")
    print(f"  Rzeczowniki m: {len(noun_lemmas['m']):,}")
    print(f"  Rzeczowniki f: {len(noun_lemmas['f']):,}")
    print(f"  Rzeczowniki n: {len(noun_lemmas['n']):,}")
    print(f"  Dopełniacze:   {len(dop_forms):,}")

    os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)

    with open(OUTPUT_ADJ, "w", encoding="utf-8") as f:
        json.dump(complete, f, ensure_ascii=False)
    print(f"\nZapisano: {OUTPUT_ADJ}")

    noun_data = {k: sorted(v) for k, v in noun_lemmas.items()}
    with open(OUTPUT_NOUN, "w", encoding="utf-8") as f:
        json.dump(noun_data, f, ensure_ascii=False, indent=2)
    print(f"Zapisano: {OUTPUT_NOUN}")

    with open(OUTPUT_DOP, "w", encoding="utf-8") as f:
        json.dump(sorted(dop_forms), f, ensure_ascii=False)
    print(f"Zapisano: {OUTPUT_DOP}")

    print("\nGotowe! Teraz możesz uruchomić generator.")


if __name__ == "__main__":
    build()
