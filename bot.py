"""
Discord bot — Generator Fraz.

Komendy:
  .random [liczba]  — generuje frazy w aktualnym trybie
  .prd              — tryb: Przymiotnik + Rzeczownik + Dopełniacz (domyślny)
  .pr               — tryb: Przymiotnik + Rzeczownik
  .rd               — tryb: Rzeczownik + Dopełniacz
  .unsafe / .safe   — toggle filtrowania treści
  .status           — aktualny tryb i filtr
  .help             — pomoc
"""
import os
import json
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
from generator import generate_phrase, MODES

load_dotenv("random_name_gen.env")
TOKEN = os.getenv("DISCORD_TOKEN")

MAX_PHRASES = 25

MODE_LABELS = {
    "adj+n+gen": "Przymiotnik + Rzeczownik + Dopełniacz",
    "adj+n":     "Przymiotnik + Rzeczownik",
    "n+gen":     "Rzeczownik + Dopełniacz",
}

_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "bot_state.json")

def _load_state():
    if os.path.exists(_STATE_PATH):
        try:
            raw  = json.load(open(_STATE_PATH, encoding="utf-8"))
            safe = {int(k): v for k, v in raw.get("safe", {}).items()}
            mode = {int(k): v for k, v in raw.get("mode", {}).items()}
            return safe, mode
        except Exception:
            pass
    return {}, {}

def _save_state():
    with open(_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "safe": {str(k): v for k, v in safe_mode.items()},
            "mode": {str(k): v for k, v in bot_mode.items()},
        }, f)

safe_mode, bot_mode = _load_state()

def is_safe(guild_id: int) -> bool:
    return safe_mode.get(guild_id, True)

def get_mode(guild_id: int) -> str:
    return bot_mode.get(guild_id, "adj+n+gen")


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"Bot zalogowany jako {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name=".random | .help"))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Wpisz liczbę, np. `.random 5`", delete_after=8)
        return
    raise error


@bot.command(name="random", aliases=["r", "gen"])
async def cmd_random(ctx, count: int = 1):
    """Generuje losowe frazy w aktualnym trybie."""
    count = max(1, count)
    if count > MAX_PHRASES:
        await ctx.send(f"❌ Maksymalnie **{MAX_PHRASES}** fraz na raz.", delete_after=8)
        return

    safe    = is_safe(ctx.guild.id)
    mode    = get_mode(ctx.guild.id)
    phrases = [generate_phrase(mode=mode, safe=safe) for _ in range(count)]

    color  = 0x1a73e8 if safe else 0xe8341a
    footer = ("🔒 Safe" if safe else "🔓 Unsafe") + f"  •  {MODE_LABELS[mode]}"
    embed  = discord.Embed(
        title="🎲 Generator Fraz",
        description="\n".join(f"• {p}" for p in phrases),
        color=color
    )
    embed.set_footer(text=footer)
    await ctx.send(embed=embed)


async def _set_mode(ctx, new_mode: str):
    bot_mode[ctx.guild.id] = new_mode
    _save_state()
    embed = discord.Embed(
        title="✅ Tryb zmieniony",
        description=f"**{MODE_LABELS[new_mode]}**\nUżyj `.random` żeby generować.",
        color=0x2d9249
    )
    await ctx.send(embed=embed, delete_after=12)

@bot.command(name="prd")
async def cmd_prd(ctx):
    """Tryb: Przymiotnik + Rzeczownik + Dopełniacz."""
    await _set_mode(ctx, "adj+n+gen")

@bot.command(name="pr")
async def cmd_pr(ctx):
    """Tryb: Przymiotnik + Rzeczownik."""
    await _set_mode(ctx, "adj+n")

@bot.command(name="rd")
async def cmd_rd(ctx):
    """Tryb: Rzeczownik + Dopełniacz."""
    await _set_mode(ctx, "n+gen")


@bot.command(name="unsafe")
async def cmd_unsafe(ctx):
    """Włącza unsafe mode dla tego serwera."""
    if not is_safe(ctx.guild.id):
        await ctx.send("🔓 Unsafe mode jest już włączony.", delete_after=6)
        return
    safe_mode[ctx.guild.id] = False
    _save_state()
    embed = discord.Embed(
        title="🔓 Unsafe mode włączony",
        description="Generator będzie teraz rzucał bez ograniczeń.\nWróć do safe mode komendą `.safe`",
        color=0xe8341a
    )
    await ctx.send(embed=embed)


@bot.command(name="safe")
async def cmd_safe(ctx):
    """Włącza safe mode dla tego serwera."""
    if is_safe(ctx.guild.id):
        await ctx.send("🔒 Safe mode jest już włączony.", delete_after=6)
        return
    safe_mode[ctx.guild.id] = True
    _save_state()
    embed = discord.Embed(
        title="🔒 Safe mode włączony",
        description="Generator filtruje teraz treści nieodpowiednie.",
        color=0x1a73e8
    )
    await ctx.send(embed=embed)


@bot.command(name="status")
async def cmd_status(ctx):
    """Pokazuje aktualny tryb bota."""
    safe  = is_safe(ctx.guild.id)
    mode  = get_mode(ctx.guild.id)
    embed = discord.Embed(title="ℹ️ Status", color=0x1a73e8 if safe else 0xe8341a)
    embed.add_field(name="Filtr", value="🔒 Safe" if safe else "🔓 Unsafe", inline=True)
    embed.add_field(name="Tryb",  value=MODE_LABELS[mode],                  inline=True)
    await ctx.send(embed=embed, delete_after=12)


@bot.command(name="help")
async def cmd_help(ctx):
    safe  = is_safe(ctx.guild.id)
    mode  = get_mode(ctx.guild.id)
    embed = discord.Embed(title="📖 Generator Fraz — pomoc", color=0x5f6368)
    embed.add_field(
        name="Generowanie",
        value="`.random` — 1 fraza\n`.random 10` — 10 fraz\n`.r 5` — skrót",
        inline=False
    )
    embed.add_field(
        name="Tryb losowania",
        value=(
            "`.prd` — Przymiotnik + Rzeczownik + Dopełniacz\n"
            "`.pr`  — Przymiotnik + Rzeczownik\n"
            "`.rd`  — Rzeczownik + Dopełniacz\n\n"
            f"Teraz: **{MODE_LABELS[mode]}**"
        ),
        inline=False
    )
    embed.add_field(
        name="Filtr treści",
        value=(
            "`.unsafe` — włącz unsafe mode\n"
            "`.safe`   — włącz safe mode\n\n"
            f"Teraz: {'🔒 safe' if safe else '🔓 unsafe'}"
        ),
        inline=False
    )
    embed.set_footer(text=f"Maks. {MAX_PHRASES} fraz na wywołanie")
    await ctx.send(embed=embed)


if __name__ == "__main__":
    if not TOKEN:
        print("BŁĄD: Brak tokenu!")
        print("Sprawdź plik random_name_gen.env — powinna być linia: DISCORD_TOKEN=twój_token")
    else:
        bot.run(TOKEN)
