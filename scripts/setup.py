"""
Krok 1: instaluje morfeusz2 i pobiera PoliMorf.
Uruchom raz przed build_database.py.
"""
import subprocess
import sys
import urllib.request
import os

POLIMORF_URL = "https://zil.ipipan.waw.pl/PoliMorf?action=AttachFile&do=get&target=PoliMorf-0.6.7.tab.gz"
# Zawsze zapisuj w głównym folderze projektu (katalog nadrzędny scripts/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLIMORF_PATH = os.path.join(PROJECT_ROOT, "PoliMorf.tab.gz")


def install_morfeusz2():
    print("Instalowanie morfeusz2...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "morfeusz2"])
    print("OK: morfeusz2 zainstalowany.\n")


def download_polimorf():
    if os.path.exists(POLIMORF_PATH):
        print(f"OK: PoliMorf już istnieje ({POLIMORF_PATH}), pomijam pobieranie.")
        return

    print(f"Pobieranie PoliMorf...")

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(downloaded / total_size * 100, 100)
            print(f"\r  {pct:.1f}%", end="", flush=True)

    try:
        urllib.request.urlretrieve(POLIMORF_URL, POLIMORF_PATH, reporthook=progress)
        print(f"\nOK: zapisano jako {POLIMORF_PATH}\n")
    except Exception as e:
        print(f"\nBłąd pobierania: {e}")
        print("Pobierz PoliMorf ręcznie ze strony: https://zil.ipipan.waw.pl/PoliMorf")
        print(f"i zapisz plik jako: {POLIMORF_PATH} (w głównym folderze projektu)")
        sys.exit(1)


if __name__ == "__main__":
    install_morfeusz2()
    download_polimorf()
    print("Gotowe! Teraz uruchom: python scripts/build_database.py")
