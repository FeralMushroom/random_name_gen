import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import threading
import tempfile
import os
import random
from gtts import gTTS
from playsound import playsound
from generator import generate_phrase_gui as generate_phrase, set_safe_mode

# ── Paleta kolorów ───────────────────────────────────────────────────────────
BG      = "#f0f2f5"   # tło okna
SURFACE = "#ffffff"   # tło kart
TEXT    = "#202124"   # główny tekst
TEXT2   = "#5f6368"   # drugi plan
ACCENT  = "#1a73e8"   # niebieski — generuj, główne akcje
A_ACT   = "#1557b0"   # hover akcentu
GREEN   = "#2d9249"   # zapisz, safe mode
G_ACT   = "#246e3b"
GREY    = "#5f6368"   # wyczyść, zaznacz
GR_ACT  = "#494c50"
PURPLE  = "#9334e6"   # TTS
P_ACT   = "#7b28c8"
BORDER  = "#dadce0"

FONT    = ("Segoe UI", 10)
FONT_SM = ("Segoe UI", 9)
FONT_LG = ("Segoe UI", 11)
FONT_H  = ("Segoe UI", 14, "bold")


def btn(parent, text, cmd, bg=ACCENT, bg_act=A_ACT, fg="white", **kw):
    """Płaski, kolorowy przycisk."""
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg, activebackground=bg_act, activeforeground=fg,
        font=FONT, relief=tk.FLAT, bd=0,
        padx=14, pady=7, cursor="hand2", **kw
    )
    return b


def card(parent, **kw):
    """Biała karta z cienką ramką."""
    outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    inner = tk.Frame(outer, bg=SURFACE, **kw)
    inner.pack(fill="both", expand=True)
    return outer, inner


# ── TTS ──────────────────────────────────────────────────────────────────────
def speak_text(text):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        gTTS(text=text, lang="pl", tld="pl").save(tmp_path)
        playsound(tmp_path)
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("TTS błąd", str(e)))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def speak_selected():
    selected = [cb.phrase for cb in checkboxes if cb.var.get()]
    if not selected:
        messagebox.showinfo("Info", "Nie zaznaczono żadnej frazy.")
        return
    btn_speak.config(state=tk.DISABLED, text="  Czyta...")

    def run():
        for phrase in selected:
            speak_text(phrase)
        root.after(0, lambda: btn_speak.config(state=tk.NORMAL, text="▶  Przeczytaj zaznaczone"))

    threading.Thread(target=run, daemon=True).start()


# ── Safe mode ────────────────────────────────────────────────────────────────
def on_safe_mode_toggle():
    enabled = var_safe_mode.get()
    if not enabled:
        confirmed = messagebox.askyesno(
            "Uwaga",
            "Wyłączasz tryb bezpieczny.\n\n"
            "Program może generować wulgaryzmy i treści\n"
            "nieodpowiednie dla szerokiej publiczności.\n\n"
            "Czy na pewno?",
            icon="warning"
        )
        if not confirmed:
            var_safe_mode.set(True)
            return
    set_safe_mode(enabled)
    lbl_safe.config(
        text="🔒 Safe mode" if enabled else "🔓 Unsafe mode",
        fg=GREEN if enabled else "#ea4335"
    )


# ── Generowanie ──────────────────────────────────────────────────────────────
def get_modes():
    modes = []
    if var_adj_n.get():     modes.append("adj+n")
    if var_adj_n_gen.get(): modes.append("adj+n+gen")
    if var_n_gen.get():     modes.append("n+gen")
    return modes or ["adj+n+gen"]


def generate_phrases():
    try:
        count = int(entry_count.get())
    except ValueError:
        messagebox.showerror("Błąd", "Wpisz poprawną liczbę!")
        return
    clear_phrases()
    modes = get_modes()
    for _ in range(count):
        phrase = generate_phrase(random.choice(modes))
        var = tk.BooleanVar()
        cb = tk.Checkbutton(
            phrases_frame, text=phrase, variable=var,
            anchor="w", justify="left",
            bg=SURFACE, fg=TEXT, font=FONT,
            activebackground="#f0f7ff",
            selectcolor=SURFACE,
            relief=tk.FLAT, bd=0,
            cursor="hand2",
        )
        cb.var = var
        cb.phrase = phrase
        cb.pack(fill="x", padx=10, pady=1, anchor="w")
        checkboxes.append(cb)
        all_phrases.append(phrase)
    update_copy_box()


def clear_phrases():
    for cb in checkboxes:
        cb.destroy()
    checkboxes.clear()
    all_phrases.clear()
    copy_box.config(state=tk.NORMAL)
    copy_box.delete("1.0", tk.END)
    copy_box.config(state=tk.DISABLED)


def select_all():
    for cb in checkboxes:
        cb.var.set(True)


def deselect_all():
    for cb in checkboxes:
        cb.var.set(False)


def save_selected():
    selected = [cb.phrase for cb in checkboxes if cb.var.get()]
    if not selected:
        messagebox.showinfo("Info", "Nie zaznaczono żadnej frazy.")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Plik tekstowy", "*.txt"), ("Wszystkie pliki", "*.*")],
        title="Zapisz zaznaczone frazy",
    )
    if not path:
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(selected))
    messagebox.showinfo("Zapisano", f"Zapisano {len(selected)} fraz:\n{path}")


def update_copy_box():
    copy_box.config(state=tk.NORMAL)
    copy_box.delete("1.0", tk.END)
    copy_box.insert(tk.END, "\n".join(all_phrases))
    copy_box.config(state=tk.DISABLED)


# ────────────────────────────────────────────────────────────────────────────
# GUI
# ────────────────────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Generator Fraz")
root.geometry("820x760")
root.configure(bg=BG)
root.minsize(600, 500)

# ── Nagłówek ──────────────────────────────────────────────────────────────────
header = tk.Frame(root, bg=ACCENT, pady=11)
header.pack(fill="x")

tk.Label(header, text="Generator Fraz", font=FONT_H, bg=ACCENT, fg="white").pack(side=tk.LEFT, padx=18)

safe_row = tk.Frame(header, bg=ACCENT)
safe_row.pack(side=tk.RIGHT, padx=18)

var_safe_mode = tk.BooleanVar(value=True)
lbl_safe = tk.Label(safe_row, text="🔒 Safe mode", font=FONT, bg=ACCENT, fg=GREEN)
lbl_safe.pack(side=tk.LEFT, padx=(0, 6))
tk.Checkbutton(
    safe_row, variable=var_safe_mode, command=on_safe_mode_toggle,
    bg=ACCENT, activebackground=ACCENT, selectcolor=A_ACT,
    relief=tk.FLAT, bd=0, cursor="hand2"
).pack(side=tk.LEFT)

# ── Panel kontrolny ───────────────────────────────────────────────────────────
tk.Label(root, text="Generowanie", font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w", padx=18, pady=(12, 2))

ctrl_outer, ctrl = card(root, padx=14, pady=10)
ctrl_outer.pack(fill="x", padx=16)

tk.Label(ctrl, text="Ile fraz:", font=FONT, bg=SURFACE, fg=TEXT).pack(side=tk.LEFT)

entry_frame = tk.Frame(ctrl, bg=BORDER, padx=1, pady=1)
entry_frame.pack(side=tk.LEFT, padx=(6, 14))
entry_count = tk.Entry(entry_frame, width=6, font=FONT_LG, relief=tk.FLAT, bd=0,
                       bg=BG, fg=TEXT, insertbackground=TEXT)
entry_count.insert(0, "10")
entry_count.pack(padx=6, pady=3)

btn(ctrl, "Generuj",  generate_phrases).pack(side=tk.LEFT, padx=(0, 6))
btn(ctrl, "Wyczyść",  clear_phrases, bg=GREY, bg_act=GR_ACT).pack(side=tk.LEFT)

# ── Tryby generacji ───────────────────────────────────────────────────────────
tk.Label(root, text="Struktura fraz", font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w", padx=18, pady=(10, 2))

modes_outer, modes_inner = card(root, padx=14, pady=8)
modes_outer.pack(fill="x", padx=16)

var_adj_n     = tk.BooleanVar(value=False)
var_adj_n_gen = tk.BooleanVar(value=True)
var_n_gen     = tk.BooleanVar(value=False)

for label, var in [
    ("Przymiotnik + Rzeczownik", var_adj_n),
    ("Przymiotnik + Rzeczownik + Dopełniacz", var_adj_n_gen),
    ("Rzeczownik + Dopełniacz", var_n_gen),
]:
    tk.Checkbutton(
        modes_inner, text=label, variable=var,
        bg=SURFACE, fg=TEXT, font=FONT,
        activebackground=SURFACE, selectcolor=SURFACE,
        relief=tk.FLAT, bd=0
    ).pack(side=tk.LEFT, padx=(0, 18))

# ── Lista fraz ────────────────────────────────────────────────────────────────
tk.Label(root, text="Wygenerowane frazy", font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w", padx=18, pady=(10, 2))

list_outer, list_inner = card(root)
list_outer.pack(fill="both", expand=True, padx=16)

scrollbar = tk.Scrollbar(list_inner, orient="vertical", bg=BORDER, troughcolor=SURFACE, width=12)
scrollbar.pack(side="right", fill="y")

phrases_canvas = tk.Canvas(list_inner, bg=SURFACE, highlightthickness=0, yscrollcommand=scrollbar.set)
phrases_canvas.pack(side="left", fill="both", expand=True)
scrollbar.config(command=phrases_canvas.yview)

phrases_frame = tk.Frame(phrases_canvas, bg=SURFACE)
canvas_win = phrases_canvas.create_window((0, 0), window=phrases_frame, anchor="nw")

phrases_frame.bind("<Configure>", lambda e: phrases_canvas.configure(scrollregion=phrases_canvas.bbox("all")))
phrases_canvas.bind("<Configure>", lambda e: phrases_canvas.itemconfig(canvas_win, width=e.width))
phrases_canvas.bind("<MouseWheel>", lambda e: phrases_canvas.yview_scroll(int(-1 * e.delta / 120), "units"))

checkboxes  = []
all_phrases = []

# ── Pasek akcji ───────────────────────────────────────────────────────────────
actions = tk.Frame(root, bg=BG, pady=8)
actions.pack(fill="x", padx=16)

btn(actions, "Zaznacz wszystkie",  select_all,   bg=GREY,   bg_act=GR_ACT).pack(side=tk.LEFT, padx=(0, 6))
btn(actions, "Odznacz wszystkie",  deselect_all, bg=GREY,   bg_act=GR_ACT).pack(side=tk.LEFT, padx=(0, 14))
btn(actions, "💾  Zapisz zaznaczone", save_selected, bg=GREEN,  bg_act=G_ACT).pack(side=tk.LEFT, padx=(0, 6))
btn_speak = btn(actions, "▶  Przeczytaj zaznaczone", speak_selected, bg=PURPLE, bg_act=P_ACT)
btn_speak.pack(side=tk.LEFT)

# ── Pole kopiowania ───────────────────────────────────────────────────────────
tk.Label(root, text="Skopiuj frazy", font=FONT_SM, bg=BG, fg=TEXT2).pack(anchor="w", padx=18, pady=(0, 2))

copy_outer, _ = card(root)
copy_outer.pack(fill="x", padx=16, pady=(0, 14))

copy_box = scrolledtext.ScrolledText(
    copy_outer, wrap=tk.WORD, height=6,
    font=FONT, relief=tk.FLAT, bd=0,
    bg=SURFACE, fg=TEXT,
    state=tk.DISABLED, padx=10, pady=6
)
copy_box.pack(fill="x")

root.mainloop()
