"""
Tagowanie słów jako safe/unsafe.

Użycie:
  python scripts/tag_words.py          # skanuje bazę i otwiera przegląd
  python scripts/tag_words.py --rescan  # wymusza ponowne skanowanie
"""
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADJ_FORMS_PATH    = os.path.join(PROJECT_ROOT, "data", "adj_forms.json")
NOUN_LEMMAS_PATH  = os.path.join(PROJECT_ROOT, "data", "noun_lemmas.json")
DOP_PATH          = os.path.join(PROJECT_ROOT, "data", "words_dop.json")
NEEDS_REVIEW_PATH = os.path.join(PROJECT_ROOT, "data", "needs_review.json")
UNSAFE_PATH       = os.path.join(PROJECT_ROOT, "data", "unsafe.json")

# ============================================================
# Lista ofensywnych rdzeni i słów.
# Sprawdzamy czy KTÓRYŚ rdzeń jest zawarty w słowie (substring).
# Uzupełnij o własne słowa jeśli coś umknie automatycznemu skanowi.
# ============================================================
OFFENSIVE_ROOTS = [
    # --- Przekleństwa ---
    "kurw",     # kurwa, kurewski, zakurwiony
    "chuj",     # chuj, chujowy
    "pizd",     # pizda, pizdowaty
    "jeba",     # jebać, jebany
    "jebi",     # jebiący
    "pierdol",  # pierdolić, pierdolony
    "pierdz",   # pierdzieć, pierdzący
    "gówn",     # gówno, gówniarz
    "sraj",     # srać (sraj- żeby nie łapać "Izrael")
    "cipk",     # cipka
    "dupek",    # dupek
    "dupci",    # dupcia
    "hujow",    # hujowy
    "wkurw",    # wkurwiony
    "nakurw",   # nakurwić
    # --- Slury rasistowskie / dyskryminacyjne ---
    "czarnuch",
    "bambus",    # używany jako slur rasistowski (też = roślina — będzie false positive)
    "żydek",     # obraźliwa forma zdrobniała
    "zydek",     # wariant bez ogonka
    "żydostw",   # żydostwo (pejoratywne)
    "zydostw",   # wariant bez ogonków
    "pedałow",   # pedałowski
    "pedalsk",   # pedalski
    "kutaf",     # slur
    # --- Silnie obraźliwe ---
    "debil",    # debil, debilny, debilizm
    "kretyn",   # kretyn, kretynizm
    "gnida",    # gnida (obraźliwe)
]


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_offensive(word: str) -> str | None:
    """Zwraca rdzeń który wyzwolił flagowanie, albo None jeśli słowo jest czyste."""
    w = word.lower()
    for root in OFFENSIVE_ROOTS:
        if root.lower() in w:
            return root
    return None


def scan():
    print("Skanowanie bazy danych...")
    adj_forms = _load(ADJ_FORMS_PATH)
    noun_data = _load(NOUN_LEMMAS_PATH)
    dop_list  = _load(DOP_PATH)["Dop"]

    flagged_adj  = []
    flagged_noun = []
    flagged_dop  = []

    for triplet in adj_forms:
        root = is_offensive(triplet[0])  # sprawdzamy formę männl. (= lemmat)
        if root:
            flagged_adj.append({"forms": triplet, "root": root})

    for gender, nouns in noun_data.items():
        for noun in nouns:
            root = is_offensive(noun)
            if root:
                flagged_noun.append({"word": noun, "gender": gender, "root": root})

    for dop in dop_list:
        root = is_offensive(dop)
        if root:
            flagged_dop.append({"word": dop, "root": root})

    result = {"adj": flagged_adj, "noun": flagged_noun, "dop": flagged_dop}
    _save(NEEDS_REVIEW_PATH, result)

    print(f"  Oflagowane przymiotniki: {len(flagged_adj):,}")
    print(f"  Oflagowane rzeczowniki:  {len(flagged_noun):,}")
    print(f"  Oflagowane dopełniacze:  {len(flagged_dop):,}")
    print(f"Zapisano do: {NEEDS_REVIEW_PATH}\n")
    return result


def review(flagged):
    # Załaduj już podjęte decyzje (jeśli przerywałeś wcześniej)
    if os.path.exists(UNSAFE_PATH):
        unsafe = _load(UNSAFE_PATH)
        unsafe.setdefault("adj", [])
        unsafe.setdefault("noun", [])
    else:
        unsafe = {"adj": [], "noun": []}

    unsafe.setdefault("dop", [])

    decided_adj  = set(unsafe["adj"])
    decided_noun = set(unsafe["noun"])
    decided_dop  = set(unsafe["dop"])

    # Filtruj już zdecydowane — możesz wznawiać w dowolnym momencie
    todo_adj  = [e for e in flagged["adj"]  if e["forms"][0] not in decided_adj]
    todo_noun = [e for e in flagged["noun"] if e["word"]    not in decided_noun]
    todo_dop  = [e for e in flagged.get("dop", []) if e["word"] not in decided_dop]

    total = len(todo_adj) + len(todo_noun) + len(todo_dop)

    if total == 0:
        print("Wszystkie oflagowane słowa już przejrzane.")
        print(f"Unsafe: {len(unsafe['adj'])} przymiotników, {len(unsafe['noun'])} rzeczowników")
        return

    print(f"Do przejrzenia: {len(todo_adj)} przymiotników + {len(todo_noun)} rzeczowników = {total} łącznie")
    print()
    print("  [U] = unsafe — zablokuj słowo")
    print("  [S] = safe   — zostaw w bazie")
    print("  [K] = skip   — pomiń, zdecyduj później")
    print("  [Q] = quit   — zapisz i wyjdź")
    print()
    input("Naciśnij Enter żeby zacząć przegląd...")

    all_entries = (
        [("adj",  e) for e in todo_adj] +
        [("noun", e) for e in todo_noun] +
        [("dop",  e) for e in todo_dop]
    )

    reviewed = 0
    for kind, entry in all_entries:
        reviewed += 1

        print("\n" + "═" * 52)

        if kind == "adj":
            m, f, n = entry["forms"]
            print(f"  [{reviewed}/{total}]  PRZYMIOTNIK")
            print(f"  Formy:  {m}  /  {f}  /  {n}")
            print(f"  Powód:  rdzeń »{entry['root']}«")
        elif kind == "noun":
            print(f"  [{reviewed}/{total}]  RZECZOWNIK  (rodzaj: {entry['gender']})")
            print(f"  Słowo:  {entry['word']}")
            print(f"  Powód:  rdzeń »{entry['root']}«")
        else:
            print(f"  [{reviewed}/{total}]  DOPEŁNIACZ")
            print(f"  Fraza:  {entry['word']}")
            print(f"  Powód:  rdzeń »{entry['root']}«")

        print()
        raw = input("  U / S / K / Q  →  ").strip().upper()

        if not raw:
            continue

        choice = raw[0]

        if choice == "Q":
            print("\nPrzerwano. Postęp zapisany.")
            break
        elif choice == "U":
            if kind == "adj":
                unsafe["adj"].append(entry["forms"][0])
            elif kind == "noun":
                unsafe["noun"].append(entry["word"])
            else:
                unsafe["dop"].append(entry["word"])
        elif choice == "S":
            pass  # słowo zostaje w bazie
        # K = skip — nie zapisujemy decyzji, pojawi się następnym razem

        # Zapis po każdej decyzji — można bezpiecznie przerwać
        _save(UNSAFE_PATH, unsafe)

    print(f"\n{'═' * 52}")
    print(f"Gotowe. Zapisano do: {UNSAFE_PATH}")
    print(f"Unsafe: {len(unsafe['adj'])} przymiotników, {len(unsafe['noun'])} rzeczowników")
    remaining = sum(
        1 for e in flagged["adj"]  if e["forms"][0] not in set(unsafe["adj"])
        and e["forms"][0] not in decided_adj
    ) + sum(
        1 for e in flagged["noun"] if e["word"] not in set(unsafe["noun"])
        and e["word"] not in decided_noun
    ) - (total - reviewed)
    if remaining > 0:
        print(f"Pominięte (K): {remaining} — uruchom skrypt ponownie żeby wrócić do nich.")


if __name__ == "__main__":
    rescan = "--rescan" in sys.argv

    if rescan and os.path.exists(NEEDS_REVIEW_PATH):
        os.remove(NEEDS_REVIEW_PATH)
        print("Usunięto stary plik przeglądu, skanuję od nowa...\n")

    if not os.path.exists(NEEDS_REVIEW_PATH):
        flagged = scan()
    else:
        flagged = _load(NEEDS_REVIEW_PATH)
        print(f"Wczytano istniejący plik przeglądu.")
        print(f"  Przymiotniki: {len(flagged['adj']):,}")
        print(f"  Rzeczowniki:  {len(flagged['noun']):,}\n")

    review(flagged)
