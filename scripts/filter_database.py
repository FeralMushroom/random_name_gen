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

MIN_FREQ_ADJ  = 2e-7
MIN_FREQ_NOUN = 5e-7
# Formy fleksyjne mają niższe freq niż lematy — próg niższy niż dla rzeczowników
MIN_FREQ_DOP  = 4e-7

# Nieregularne liczebniki porządkowe (regularne łapie RE_ORDINAL)
ORDINAL_BLACKLIST = {
    "pierwszy", "trzeci", "czwarty", "piąty", "szósty",
    "siódmy", "ósmy", "dziewiąty", "dziesiąty", "zerowy",
}
RE_ORDINAL    = re.compile(r"(nasty|dziesty|dziesiąty|setny|tysięczny|milionowy)$")
RE_PARTICIPLE = re.compile(r"ący$")  # imiesłowy czynne — brzmią jak opis czynności
RE_FOREIGN    = re.compile(r"[xvqXVQ]")  # litery obce polskiemu alfabetowi
# Przymiotniki nazwiskowe/miejscowe — wyższy próg częstości żeby zostały tylko powszechnie znane
RE_GEO_ADJ    = re.compile(r"(owski|ewski|ański|iński|yński)$")

# Rzeczowniki do usunięcia
NOUN_BLACKLIST = {
    # błędy PoliMorfa / archaizmy / gwara
    "staje", "recept", "starka", "padło", "drugie", "należący", "wiec",
    "lucerna", "tera",
    # marki samochodowe
    "audi", "bentley", "bugatti", "buick", "cadillac", "chrysler", "clio",
    "daewoo", "dodge", "ferrari", "fiat", "ford", "honda", "hyundai",
    "lamborghini", "lancia", "mazda", "mclaren", "mercedes", "mitsubishi",
    "nissan", "opel", "peugeot", "plymouth", "pontiac", "porsche", "renault",
    "saab", "seat", "skoda", "subaru", "suzuki", "toyota",
    # marki tech / elektronika
    "acer", "android", "canon", "dell", "ericsson", "intel", "kodak",
    "motorola", "nikon", "nokia", "philips", "samsung", "siemens", "sony",
    # inne marki i firmy
    "adidas", "allegro", "blizzard", "empik", "jacobs", "jacuzzi", "lego",
    "marlboro", "milka", "nike", "pepsi", "scrabble", "shell", "tabasco",
    "trojan", "tymbark", "yale", "yamaha",
    # zespoły / artyści
    "abba", "beatles", "doors",
    # imiona i nazwiska (zostawiamy: albert, abdul, donald, einstein, frankenstein, janusz, adolf, hitler)
    "alim", "amelia", "angelika", "antek", "daniel", "danko", "darek",
    "gabriela", "jarek", "jarka", "jasiek", "jola", "jonasz", "jung",
    "karolek", "kowalczyk", "lucyfer", "lynch", "maciek", "majka", "maks",
    "marcelina", "marek", "miranda", "morris", "newton", "nowak", "remington",
    "robinson", "sabina", "sherlock", "tarzan", "wanda", "weber", "weronika",
    "wiktor", "wiktoria", "wojtek",
    # niebędące polskimi miastami nazwy geograficzne
    "austin", "boston", "bristol", "brytania", "bukowina", "disneyland",
    "granada", "hawana", "ibiza", "kabul", "kingston", "lincoln", "lucerna",
    "malaga", "manchester", "manila", "orlean", "pekin", "toledo", "tybet",
    "york",
    # nazwy stanów USA
    "dakota", "arizona", "wirginia", "delaware", "teksas", "kolorado",
    # angielskie i inne obce loanwordy
    "anthem", "background", "backup", "band", "banner", "barbecue", "bean",
    "beat", "bias", "billboard", "blackout", "blind", "body", "boogie",
    "boom", "boot", "business", "buster", "camera", "camp", "cargo",
    "castor", "catch", "causa", "challenge", "challenger", "chart", "chat",
    "cherry", "chief", "citizen", "city", "clip", "clown", "coca", "collage",
    "college", "compact", "consulting", "continental", "copyright", "corner",
    "counter", "country", "crack", "cricket", "cross", "crown", "cruiser",
    "dancing", "desert", "design", "designer", "display", "draft", "drag",
    "dual", "earl", "eastern", "engineering", "ensemble", "enter", "error",
    "establishment", "feedback", "feeling", "field", "fighter", "firefly",
    "flip", "flower", "focus", "football", "full", "funky", "fusion",
    "gateway", "gentleman", "green", "guide", "happening", "hardcore",
    "hardware", "highway", "image", "independent", "industrial", "insert",
    "insider", "interface", "interior", "iron", "jack", "jeans", "joint",
    "kaiser", "kapo", "keyboard", "king", "konklawe", "layout", "lead",
    "leader", "light", "lingua", "lion", "lobby", "long", "loop", "lord",
    "luter", "madame", "mademoiselle", "mainstream", "management", "manager",
    "master", "meeting", "memorandum", "millennium", "mirror", "mobile",
    "modern", "monsieur", "moon", "musli", "network", "news", "newsletter",
    "paintball", "pedicure", "peeling", "performance", "personal", "petit",
    "pool", "popular", "publishing", "ranger", "rangers", "real", "relief",
    "remake", "report", "return", "reunion", "ringo", "roll", "roller",
    "rolling", "root", "scratch", "screen", "script", "security", "september",
    "setup", "sherry", "shift", "shire", "shop", "shopping", "sleep",
    "sleeping", "slip", "soccer", "soft", "software", "solid", "song", "soul",
    "soundtrack", "sous", "speech", "speed", "speedway", "spring", "sprinter",
    "standing", "star", "stuff", "suahili", "sunny", "support", "sweet",
    "swift", "swing", "talk", "tall", "target", "team", "teaser", "tell",
    "timing", "tips", "tournee", "track", "trailer", "treatment", "trek",
    "trial", "trick", "trip", "troll", "truck", "trust", "underground",
    "unit", "upgrade", "vintage", "wellington", "workshop", "yang", "yard",
}

DOP_BLACKLIST = {
    # błędy fleksyjne PoliMorfa
    "joga", "zorza", "brzydula", "sukienka", "ciosy", "metrowej",
    # imiona / nazwy własne w dopełniaczu
    "bona", "toni", "yang", "ringo", "jarka", "jola", "sabina",
    # marki i loanwordy w dopełniaczu
    "audi", "bugatti", "clio", "daewoo", "ferrari", "lamborghini",
    "marlboro", "mitsubishi", "nike", "porsche", "renault", "scrabble",
    "sony", "subaru", "suzuki", "tabasco", "yale",
    "barbecue", "body", "boogie", "cargo", "challenge", "cherry", "city",
    "country", "feedback", "firefly", "funky", "fusion", "image", "jacuzzi",
    "light", "lingua", "lobby", "madame", "mademoiselle", "mobile",
    "monsieur", "script", "security", "soul", "sous", "suahili", "sunny",
    # pozostałe wcześniejsze wpisy
    "delaware", "kolorado", "kapo", "wiecu", "memorandum", "aids",
    "sherry", "konklawe", "paschy", "cherokee", "tournee",
    "toledo",
}

# Zaimki i determinanty które PoliMorf taguje jako przymiotniki
ADJ_BLACKLIST = {
    # zaimki wskazujące
    "ten", "ta", "to", "tamten", "tamta", "tamto",
    "ów", "ow", "owa", "owo", "owy",
    # zaimki dzierżawcze
    "mój", "moja", "moje", "twój", "twoja", "twe",
    "nasz", "nasza", "nasze", "wasz", "wasza", "wasze",
    "swój", "swoja", "swoje",
    # zaimki nieokreślone i pytające
    "jakikolwiek", "jakakolwiek", "jakiekolwiek",
    "którykolwiek", "którakolwiek", "którekolwiek",
    "jakiś", "jakaś", "jakieś",
    "któryś", "któraś", "któreś",
    "czyj", "czyjś",
    # liczebniki / determinanty
    "jeden", "jedna", "jedno",
    "każdy", "każda", "każde",
    "żaden", "żadna", "żadne",
    "sam", "sama", "samo",
    "inny", "inna", "inne",
    "drugi", "druga", "drugie",
    "pewien", "pewna", "pewne",
    # archaiczne / techniczne przymiotniki które brzmią źle
    "kontent", "kontenta", "kontente",
    "metrowy", "metrowa", "metrowe",
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
    return (
        "-" not in word
        and len(word) <= MAX_DOP_LEN
        and freq(word) >= MIN_FREQ_DOP
        and not RE_FOREIGN.search(word)
        and word.lower() not in DOP_BLACKLIST
    )


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
        if RE_PARTICIPLE.search(m):
            continue
        if RE_FOREIGN.search(m):
            continue
        # Nazwiskowe/miejscowe -owski itd. — zostają tylko jeśli są naprawdę pospolite
        if RE_GEO_ADJ.search(m) and freq(m) < 1e-5:
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

    # Zbiór wszystkich form przymiotnikowych — rzeczowniki które są w tym zbiorze
    # to substantywizowane przymiotniki (np. "puste", "chore") — wywalamy je
    adj_forms_set = {form for triplet in adj_ok for form in triplet}

    nouns_ok = {}
    total_in = total_out = 0
    for gender, words in nouns.items():
        kept = []
        for w in words:
            total_in += 1
            if "-" in w or len(w) > MAX_NOUN_LEN or freq(w) < MIN_FREQ_NOUN:
                continue
            if RE_FOREIGN.search(w):
                continue
            if w in adj_forms_set:  # substantywizowany przymiotnik
                continue
            if w in NOUN_BLACKLIST:
                continue
            kept.append(w)
            total_out += 1
        nouns_ok[gender] = kept
    print(f"  {total_in:,} -> {total_out:,}  (usunieto {total_in-total_out:,})")
    for g, words in nouns_ok.items():
        print(f"    {g}: {len(words):,}")

    # Słowa których nie ma w PoliMorfie — dodajemy ręcznie po filtrowaniu
    NOUN_ADDITIONS = {
        "m": ["janusz", "adolf", "hitler"],
        "f": ["europa", "azja", "ameryka", "australia"],
    }
    for gender, words in NOUN_ADDITIONS.items():
        existing = set(nouns_ok.get(gender, []))
        added = [w for w in words if w not in existing]
        nouns_ok.setdefault(gender, []).extend(added)
        if added:
            print(f"  Dodano do {gender}: {added}")
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
