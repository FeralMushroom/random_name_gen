"""
Porównuje stary words_dop.json z nową bazą dop_forms.json (z PoliMorfa).
Słowa których NIE MA w PoliMorfie zapisuje do data/custom_dop.json —
żebyś mógł je przejrzeć i ewentualnie dołączyć do nowej bazy.

Uruchom PO build_database.py (potrzebuje dop_forms.json).
"""
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OLD_DOP_PATH    = os.path.join(PROJECT_ROOT, "data", "words_dop.json")
NEW_DOP_PATH    = os.path.join(PROJECT_ROOT, "data", "dop_forms.json")
CUSTOM_DOP_PATH = os.path.join(PROJECT_ROOT, "data", "custom_dop.json")


def main():
    if not os.path.exists(NEW_DOP_PATH):
        print("Błąd: nie znaleziono dop_forms.json")
        print("Najpierw uruchom: python scripts/build_database.py")
        return

    with open(OLD_DOP_PATH, encoding="utf-8") as f:
        old_dop = json.load(f)["Dop"]

    with open(NEW_DOP_PATH, encoding="utf-8") as f:
        new_dop_set = {w.lower() for w in json.load(f)}

    # Szukamy słów ze starej listy których nie ma w PoliMorfie
    # Porównujemy case-insensitive bo stara lista ma wielkie litery
    unique = []
    in_polimorf = []

    for word in old_dop:
        if word.lower() in new_dop_set:
            in_polimorf.append(word)
        else:
            unique.append(word)

    print(f"Stara lista:        {len(old_dop):,} słów")
    print(f"W PoliMorfie:       {len(in_polimorf):,} słów")
    print(f"Unikalne (custom):  {len(unique):,} słów")
    print()
    print("Przykłady unikalnych słów:")
    for w in unique[:20]:
        print(f"  {w}")

    with open(CUSTOM_DOP_PATH, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"\nZapisano do: {CUSTOM_DOP_PATH}")
    print("Przejrzyj ten plik — możesz wrzucić te słowa do nowej bazy jeśli chcesz.")


if __name__ == "__main__":
    main()
