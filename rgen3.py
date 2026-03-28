import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import json
import os
import pyttsx3

# === Funkcja do ładowania plików JSON ===
def load_words(filename):
    path = os.path.join("data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# === Wczytanie danych ===
data_adj = load_words("words_przymiotniki.json")
rzeczowniki_data = load_words("words_rzeczowniki.json")
dopelnienia = load_words("words_dop.json")["Dop"]

available_ending_keys = ["a", "i", "y", "e"]

# === Generowanie pojedynczej frazy ===
def generate_phrase():
    ending_key = random.choice(available_ending_keys)
    adjectives = data_adj.get(ending_key, [])
    if not adjectives:
        return generate_phrase()
    adj = random.choice(adjectives)

    if ending_key == "a":
        gender = "f"
    elif ending_key == "e":
        gender = "n"
    else:
        gender = "m"

    noun = random.choice(rzeczowniki_data["singular"][gender])
    dop = random.choice(dopelnienia)

    return f"{adj.capitalize()} {noun} {dop}" if dop.strip() else f"{adj.capitalize()} {noun}"

# === TTS ===
def speak_text(text):
    engine = pyttsx3.init()
    for voice in engine.getProperty('voices'):
        if "polish" in voice.name.lower() or "pl" in voice.id.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.say(text)
    engine.runAndWait()

# === GUI Funkcje ===
def generate_phrases():
    try:
        count = int(entry_count.get())
        clear_phrases()
        all_phrases.clear()
        for _ in range(count):
            phrase = generate_phrase()
            var = tk.BooleanVar()
            checkbox = tk.Checkbutton(phrases_frame, text=phrase, variable=var, anchor="w", justify="left")
            checkbox.var = var
            checkbox.phrase = phrase
            checkbox.pack(fill='x', padx=5, anchor='w')
            checkboxes.append(checkbox)
            all_phrases.append(phrase)
        update_copy_box()
    except ValueError:
        messagebox.showerror("Błąd", "Wpisz poprawną liczbę!")

def clear_phrases():
    for cb in checkboxes:
        cb.destroy()
    checkboxes.clear()
    all_phrases.clear()
    copy_box.config(state=tk.NORMAL)
    copy_box.delete("1.0", tk.END)
    copy_box.config(state=tk.DISABLED)

def speak_selected():
    selected = [cb.phrase for cb in checkboxes if cb.var.get()]
    if not selected:
        messagebox.showinfo("Info", "Nie zaznaczono żadnej frazy.")
        return
    for phrase in selected:
        speak_text(phrase)

def update_copy_box():
    copy_box.config(state=tk.NORMAL)
    copy_box.delete("1.0", tk.END)
    for phrase in all_phrases:
        copy_box.insert(tk.END, phrase + "\n")
    copy_box.config(state=tk.DISABLED)

# === GUI Setup ===
root = tk.Tk()
root.title("Generator Fraz")
root.geometry("750x700")

frame = tk.Frame(root)
frame.pack(pady=10)

label_count = tk.Label(frame, text="Ile fraz?")
label_count.pack(side=tk.LEFT, padx=5)

entry_count = tk.Entry(frame, width=10)
entry_count.insert(0, "10")
entry_count.pack(side=tk.LEFT)

btn_generate = tk.Button(frame, text="GENERUJ", command=generate_phrases)
btn_generate.pack(side=tk.LEFT, padx=5)

btn_clear = tk.Button(frame, text="WYCZYŚĆ", command=clear_phrases)
btn_clear.pack(side=tk.LEFT)

btn_speak = tk.Button(frame, text="PRZECZYTAJ ZAZNACZONE", command=speak_selected)
btn_speak.pack(side=tk.LEFT, padx=5)

# === FRAZY z checkboxami ===
phrases_canvas = tk.Canvas(root, height=300)
phrases_canvas.pack(fill='both', expand=False)

scrollbar = tk.Scrollbar(root, orient="vertical", command=phrases_canvas.yview)
scrollbar.pack(side="right", fill="y")

phrases_canvas.configure(yscrollcommand=scrollbar.set)
phrases_canvas.bind('<Configure>', lambda e: phrases_canvas.configure(scrollregion=phrases_canvas.bbox("all")))

phrases_frame = tk.Frame(phrases_canvas)
phrases_canvas.create_window((0, 0), window=phrases_frame, anchor="nw")

checkboxes = []
all_phrases = []

# === POLE DO KOPIOWANIA ===
label_copy = tk.Label(root, text="Skopiuj frazy poniżej:")
label_copy.pack(pady=(10,0))

copy_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=12, state=tk.DISABLED)
copy_box.pack(padx=10, pady=5)

root.mainloop()
