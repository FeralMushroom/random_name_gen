"""
Launcher bota — uruchamia bota w tle i pokazuje okienko z logiem.
Zamknięcie okna = zatrzymanie bota.

Uruchom dwuklikiem (Windows nie pokaże konsoli).
"""
import sys
import os
import threading
import tkinter as tk
from tkinter import scrolledtext

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class _Redirect:
    """Przekierowuje stdout/stderr do widgetu tekstowego."""
    def __init__(self, widget: scrolledtext.ScrolledText):
        self._w = widget

    def write(self, text: str):
        self._w.after(0, self._append, text)

    def _append(self, text: str):
        self._w.config(state=tk.NORMAL)
        self._w.insert(tk.END, text)
        self._w.see(tk.END)
        self._w.config(state=tk.DISABLED)

    def flush(self):
        pass


root = tk.Tk()
root.title("Generator Fraz — Bot")
root.geometry("600x400")
root.configure(bg="#1e1e2e")
root.resizable(True, True)

header = tk.Frame(root, bg="#1a73e8", pady=8)
header.pack(fill="x")
tk.Label(header, text="Generator Fraz — Discord Bot",
         font=("Segoe UI", 12, "bold"), bg="#1a73e8", fg="white").pack(side=tk.LEFT, padx=14)

status_var = tk.StringVar(value="⏳ Uruchamianie...")
tk.Label(header, textvariable=status_var,
         font=("Segoe UI", 10), bg="#1a73e8", fg="#cfe2ff").pack(side=tk.RIGHT, padx=14)

log = scrolledtext.ScrolledText(
    root, state=tk.DISABLED,
    bg="#13131f", fg="#c9d1d9",
    font=("Consolas", 9),
    relief=tk.FLAT, bd=0,
    padx=8, pady=6
)
log.pack(fill="both", expand=True, padx=4, pady=4)

btn_stop = tk.Button(
    root, text="⏹  Zatrzymaj bota",
    font=("Segoe UI", 10), bg="#e8341a", fg="white",
    activebackground="#b52a14", activeforeground="white",
    relief=tk.FLAT, bd=0, padx=14, pady=7, cursor="hand2",
    command=lambda: os._exit(0)
)
btn_stop.pack(pady=(0, 8))

sys.stdout = _Redirect(log)
sys.stderr = _Redirect(log)


def _run_bot():
    import bot as bot_module
    if not bot_module.TOKEN:
        print("BŁĄD: Brak tokenu w pliku random_name_gen.env")
        status_var.set("❌ Brak tokenu")
        return

    @bot_module.bot.listen("on_ready")
    async def _on_ready_gui():
        root.after(0, status_var.set, f"✅ Online: {bot_module.bot.user}")

    try:
        bot_module.bot.run(bot_module.TOKEN)
    except Exception as e:
        print(f"Błąd bota: {e}")
        root.after(0, status_var.set, "❌ Błąd — sprawdź log")


threading.Thread(target=_run_bot, daemon=True).start()

root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
root.mainloop()
