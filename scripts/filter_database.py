"""
Filtruje bazy danych wg długości słów i częstości w języku polskim (wordfreq).

Tworzy backup w data/backup/ (jeśli jeszcze nie istnieje), potem nadpisuje:
  data/adj_forms.json
  data/noun_lemmas.json
  data/dop_forms.json
  data/custom_dop.json

Oryginały (pełne, z PoliMorfa) zawsze zostają w data/backup/.

Wymagania:
  pip install wordfreq
"""
import json
import os
import re
import shutil
from wordfreq import word_frequency

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")
BACKUP_DIR   = os.path.join(DATA_DIR, "backup")

MAX_ADJ_LEN  = 18
MAX_NOUN_LEN = 15
MAX_DOP_LEN  = 18

MIN_FREQ_ADJ  = 1e-7
MIN_FREQ_NOUN = 1e-7
# Formy fleksyjne mają niższe freq niż lematy — próg celowo niski
MIN_FREQ_DOP  = 1e-7

# Nieregularne liczebniki porządkowe (regularne łapie RE_ORDINAL)
ORDINAL_BLACKLIST = {
    "pierwszy", "trzeci", "czwarty", "piąty", "szósty",
    "siódmy", "ósmy", "dziewiąty", "dziesiąty", "zerowy",
}
RE_ORDINAL = re.compile(r"(nasty|dziesty|setny|tysięczny|milionowy)$")

# Zaimki i determinanty które PoliMorf taguje jako przymiotniki
ADJ_BLACKLIST = {
    "jakikolwiek", "jakakolwiek", "jakiekolwiek",
    "którykolwiek", "którakolwiek", "którekolwiek",
    "jakiś", "jakaś", "jakieś",
    "któryś", "któraś", "któreś",
    "czyj", "czyjś",
    "jeden", "jedna", "jedno",
    "każdy", "każda", "każde",
    "żaden", "żadna", "żadne",
    "sam", "sama", "samo",
    "ten", "ta", "to",
    "tamten", "tamta", "tamto",
    "ów", "ow", "owa", "owo", "owy",
    "inny", "inna", "inne",
    "drugi", "druga", "drugie",
    "pewien", "pewna", "pewne",
}


def load(filename):
    with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


def save(filename, data):
    with open(os.path.join(DATA_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def backup(filename):
    src = os.path.join(DATA_DIR, filename)
    dst = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f"  Backup: {filename}")
    else:
        print(f"  Backup już istnieje: {filename} — pomijam")


def freq(word):
    return word_frequency(word.lower(), "pl")


def dop_ok(word):
    return "-" not in word and len(word) <= MAX_DOP_LEN and freq(word) >= MIN_FREQ_DOP


def main():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    for f in ("adj_forms.json", "noun_lemmas.json", "dop_forms.json", "custom_dop.json"):
        backup(f)
    print()

    print("Filtruje przymiotniki...")
    with open(os.path.join(BACKUP_DIR, "adj_forms.json"), encoding="utf-8") as fh:
        adj_src = json.load(fh)
    adj_ok = []
    for triplet in adj_src:
        m = triplet[0]
        if triplet[0] == triplet[1] == triplet[2]:  # nieodmienne — błędna zgodność rodzajowa
            continue
        if m in ADJ_BLACKLIST:
            continue
        if m in ORDINAL_BLACKLIST or RE_ORDINAL.search(m):
            continue
        if "-" in m:
            continue
        if len(m) > MAX_ADJ_LEN:
            continue
        if freq(m) < MIN_FREQ_ADJ:
            continue
        adj_ok.append(triplet)
    print(f"  {len(adj_src):,} -> {len(adj_ok):,}  (usunieto {len(adj_src)-len(adj_ok):,})")
    save("adj_forms.json", adj_ok)

    print("Filtruje rzeczowniki...")
    with open(os.path.join(BACKUP_DIR, "noun_lemmas.json"), encoding="utf-8") as fh:
        nouns = json.load(fh)
    nouns_ok = {}
    total_in = total_out = 0
    for gender, words in nouns.items():
        kept = []
        for w in words:
            total_in += 1
            if "-" in w or len(w) > MAX_NOUN_LEN or freq(w) < MIN_FREQ_NOUN:
                continue
            kept.append(w)
            total_out += 1
        nouns_ok[gender] = kept
    print(f"  {total_in:,} -> {total_out:,}  (usunieto {total_in-total_out:,})")
    for g, words in nouns_ok.items():
        print(f"    {g}: {len(words):,}")
    save("noun_lemmas.json", nouns_ok)

    print("Filtruje dopelniacze...")
    with open(os.path.join(BACKUP_DIR, "dop_forms.json"), encoding="utf-8") as fh:
        dop_all = json.load(fh)
    dop_filtered = [d for d in dop_all if dop_ok(d)]
    print(f"  {len(dop_all):,} -> {len(dop_filtered):,}  (usunieto {len(dop_all)-len(dop_filtered):,})")
    save("dop_forms.json", dop_filtered)

    print("Filtruje custom_dop...")
    custom_backup = os.path.join(BACKUP_DIR, "custom_dop.json")
    if os.path.exists(custom_backup):
        with open(custom_backup, encoding="utf-8") as fh:
            custom_all = json.load(fh)
        custom_filtered = [w for w in custom_all if dop_ok(w)]
        print(f"  {len(custom_all):,} -> {len(custom_filtered):,}  (usunieto {len(custom_all)-len(custom_filtered):,})")
        save("custom_dop.json", custom_filtered)
    else:
        print("  Brak pliku custom_dop.json — pomijam")

    print("\nGotowe! Oryginaly zachowane w data/backup/")
    print("Zeby przywrocic: skopiuj pliki z data/backup/ do data/")


if __name__ == "__main__":
    main()
