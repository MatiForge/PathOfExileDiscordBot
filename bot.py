import discord
from discord.ext import commands
import json
import os
import random
from aiohttp import web
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(command_prefix="!", intents=intents)


DATA_FILE = "data.json"
FOLDER_STRONY = "strona bota"

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            if os.path.getsize(DATA_FILE) > 0:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    except (json.JSONDecodeError, FileNotFoundError):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)



async def handle_index(request):
    sciezka = os.path.join(FOLDER_STRONY, "index.html")
    if os.path.exists(sciezka):
        return web.FileResponse(sciezka)
    return web.Response(text=f"Brak pliku index.html w folderze '{FOLDER_STRONY}'!", status=404)

async def handle_css(request):
    sciezka = os.path.join(FOLDER_STRONY, "style.css")
    if os.path.exists(sciezka):
        return web.FileResponse(sciezka)
    return web.Response(text=f"Brak pliku style.css w folderze '{FOLDER_STRONY}'!", status=404)

async def handle_json(request):
    if os.path.exists(DATA_FILE):
        response = web.FileResponse(DATA_FILE)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return web.json_response({})

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/data.json', handle_json)
    app.router.add_static('/', path=r"C:\Users\xyziu\Desktop\discord_bot\strona bota", show_index=False)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("🌐 Serwer WWW uruchomiony na http://localhost:8000")

@bot.event
async def on_ready():
    print(f"🤖 Logowanie pomyślne jako {bot.user.name}")
    print(f"📂 Baza danych {DATA_FILE} jest gotowa.")
    bot.loop.create_task(start_web_server())



@bot.command()
async def save(ctx, *, message: str):
    data = load_data()
    user_id = str(ctx.author.id)
    data[user_id] = message
    save_data(data)
    await ctx.send(f"✅ Saved your data, {ctx.author.mention}!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, argument: str):
    if argument.lower() == "all":
        komunikat = await ctx.send("🧹 *Rozpoczynam masowe czyszczenie całego kanału... Może to chwilę potrwać.*")
        wyczyszczone = await ctx.channel.purge(limit=None)
        liczba_wiadomosci = len(wyczyszczone)
        sukces = await ctx.send(f"✨ Kanał został całkowicie wyczyszczony! (Wymieciono {liczba_wiadomosci} wiadomości)")
        await sukces.delete(delay=5)
        return

    try:
        ilosc = int(argument)
        await ctx.channel.purge(limit=ilosc + 1)
        komunikat = await ctx.send(f"🧹 Usunięto {ilosc} wiadomości!")
        await komunikat.delete(delay=3)
    except ValueError:
        await ctx.send(f"❌ {ctx.author.mention}, niepoprawny argument! Wpisz liczbę wiadomości (np. `!clear 10`) lub `!clear all`.")

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ {ctx.author.mention}, nie masz uprawnień do zarządzania wiadomościami (Manage Messages)!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ {ctx.author.mention}, musisz podać liczbę wiadomości lub słowo `all`! Np. `!clear 10`")



@bot.command()
async def lost(ctx, *, wiadomosc: str):
    data = load_data()
    user_name = str(ctx.author.name)
    czyste_czesci = wiadomosc.lower().replace("and", " ").replace("+", " ").split()
    
    dodane_divines = 0
    dodane_mirrors = 0
    znaleziono_walute = False

    for czesc in czyste_czesci:
        liczba_str = "".join(filter(str.isdigit, czesc))
        if len(liczba_str) > 0:
            liczba = int(liczba_str)
            if czesc.endswith("m"):
                dodane_mirrors += liczba
                znaleziono_walute = True
            elif czesc.endswith("d") or (czesc == czyste_czesci[-1] and len(czyste_czesci) == 1):
                dodane_divines += liczba
                znaleziono_walute = True

    if not znaleziono_walute:
        blad = await ctx.send(f"❌ {ctx.author.mention}, nie zrozumiałem kwoty! Użyj np. `1M and 200d`, `200d` lub `1M`.")
        try: await ctx.message.delete(delay=5)
        except: pass
        await blad.delete(delay=5)
        return

    if user_name not in data or not isinstance(data[user_name], dict):
        data[user_name] = {"divines": 0, "mirrors": 0, "win_divines": 0, "win_mirrors": 0}

   
    data[user_name]["avatar_url"] = str(ctx.author.display_avatar.url)

    if "divines" not in data[user_name]: data[user_name]["divines"] = 0
    if "mirrors" not in data[user_name]: data[user_name]["mirrors"] = 0
    if "win_divines" not in data[user_name]: data[user_name]["win_divines"] = 0
    if "win_mirrors" not in data[user_name]: data[user_name]["win_mirrors"] = 0

    data[user_name]["divines"] += dodane_divines
    data[user_name]["mirrors"] += dodane_mirrors
    save_data(data)
    
    co_wtopiono = []
    if dodane_mirrors > 0: co_wtopiono.append(f"**{dodane_mirrors} Mirrorów**")
    if dodane_divines > 0: co_wtopiono.append(f"**{dodane_divines} Divine'ów**")
    tekst_wtopione = " i ".join(co_wtopiono)

    stan_konta = f"`{data[user_name]['divines']} Divine'ów`"
    if data[user_name]["mirrors"] > 0:
        stan_konta = f"`{data[user_name]['mirrors']} Mirrorów` i " + stan_konta

    embed = discord.Embed(
        title="📉 ZAPISANO STRATĘ",
        description=f"frajer {ctx.author.mention} XDDD\nWłaśnie wtopiłeś {tekst_wtopione}.",
        color=0xff4f4f
    )
    embed.add_field(name="🔴 Twoje łączne straty to teraz:", value=stan_konta, inline=False)
    embed.set_footer(text="Wiadomość zniknie automatycznie za 10 sekund...")

    odpowiedz = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=10)
    except: pass
    await odpowiedz.delete(delay=10)

@bot.command()
async def win(ctx, *, wiadomosc: str):
    data = load_data()
    user_name = str(ctx.author.name)
    czyste_czesci = wiadomosc.lower().replace("and", " ").replace("+", " ").split()
    
    dodane_divines = 0
    dodane_mirrors = 0
    znaleziono_walute = False

    for czesc in czyste_czesci:
        liczba_str = "".join(filter(str.isdigit, czesc))
        if len(liczba_str) > 0:
            liczba = int(liczba_str)
            if czesc.endswith("m"):
                dodane_mirrors += liczba
                znaleziono_walute = True
            elif czesc.endswith("d") or (czesc == czyste_czesci[-1] and len(czyste_czesci) == 1):
                dodane_divines += liczba
                znaleziono_walute = True

    if not znaleziono_walute:
        blad = await ctx.send(f"❌ {ctx.author.mention}, nie zrozumiałem kwoty! Użyj np. `200d` lub `1M`.")
        try: await ctx.message.delete(delay=5)
        except: pass
        await blad.delete(delay=5)
        return

    if user_name not in data or not isinstance(data[user_name], dict):
        data[user_name] = {"divines": 0, "mirrors": 0, "win_divines": 0, "win_mirrors": 0}
    
    
    data[user_name]["avatar_url"] = str(ctx.author.display_avatar.url)

    if "divines" not in data[user_name]: data[user_name]["divines"] = 0
    if "mirrors" not in data[user_name]: data[user_name]["mirrors"] = 0
    if "win_divines" not in data[user_name]: data[user_name]["win_divines"] = 0
    if "win_mirrors" not in data[user_name]: data[user_name]["win_mirrors"] = 0

    data[user_name]["win_divines"] += dodane_divines
    data[user_name]["win_mirrors"] += dodane_mirrors
    save_data(data)
  
    co_wygrano = []
    if dodane_mirrors > 0: co_wygrano.append(f"**{dodane_mirrors} Mirrorów**")
    if dodane_divines > 0: co_wygrano.append(f"**{dodane_divines} Divine'ów**")
    tekst_wygrane = " i ".join(co_wygrano)

    stan_wygranych = f"`{data[user_name]['win_divines']} Divine'ów`"
    if data[user_name]["win_mirrors"] > 0:
        stan_wygranych = f"`{data[user_name]['win_mirrors']} Mirrorów` i " + stan_wygranych

    embed = discord.Embed(
        title="📈 ZAPISANO ZYSK",
        description=f"GG {ctx.author.mention}! Ktoś tu ma farta XDDD\nWłaśnie zyskałeś {tekst_wygrane}.",
        color=0x00ff87
    )
    embed.add_field(name="🟢 Twoje łączne wygrane to teraz:", value=stan_wygranych, inline=False)
    embed.set_footer(text="Wiadomość zniknie automatycznie za 10 sekund...")

    odpowiedz = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=10)
    except: pass
    await odpowiedz.delete(delay=10)

@bot.command()
async def stats(ctx):
    data = load_data()
    user_name = str(ctx.author.name)
    
    if user_name not in data or not isinstance(data[user_name], dict):
        blad = await ctx.send(f"🕊️ {ctx.author.mention}, Twoje konto w bazie jest czyste!")
        try: await ctx.message.delete(delay=5)
        except: pass
        await blad.delete(delay=5)
        return

    lost_divs = data[user_name].get("divines", 0)
    lost_mirrors = data[user_name].get("mirrors", 0)
    win_divs = data[user_name].get("win_divines", 0)
    win_mirrors = data[user_name].get("win_mirrors", 0)

    if lost_divs == 0 and lost_mirrors == 0 and win_divs == 0 and win_mirrors == 0:
        blad = await ctx.send(f"🕊️ {ctx.author.mention}, brak operacji hazardowych.")
        try: await ctx.message.delete(delay=5)
        except: pass
        await blad.delete(delay=5)
        return

    bilans_divs = win_divs - lost_divs
    bilans_mirrors = win_mirrors - lost_mirrors

    tekst_lost = f"`{lost_divs} Divine'ów`"
    if lost_mirrors > 0: tekst_lost = f"`{lost_mirrors} Mirrorów` i " + tekst_lost

    tekst_win = f"`{win_divs} Divine'ów`"
    if win_mirrors > 0: tekst_win = f"`{win_mirrors} Mirrorów` i " + tekst_win

    tekst_bilans = ""
    if bilans_mirrors > 0: tekst_bilans += f"`+{bilans_mirrors} Mirrorów` "
    elif bilans_mirrors < 0: tekst_bilans += f"`{bilans_mirrors} Mirrorów` "

    if bilans_divs > 0: tekst_bilans += f"`+{bilans_divs} Divine'ów`"
    elif bilans_divs < 0: tekst_bilans += f"`{bilans_divs} Divine'ów`"
    elif bilans_divs == 0 and tekst_bilans == "": tekst_bilans += f"`0 Divine'ów`"

    if bilans_mirrors > 0 or (bilans_mirrors == 0 and bilans_divs > 0):
        status = "📈 **OGÓLNY BILANS: ZYSK** 🤑"
        kolor = 0x00ff87
    elif bilans_mirrors < 0 or (bilans_mirrors == 0 and bilans_divs < 0):
        status = "📉 **OGÓLNY BILANS: STRATA** 💀 (Totalny frajer XDDD)"
        kolor = 0xff4f4f
    else:
        status = "⚖️ **OGÓLNY BILANS: WYCHODZISZ NA ZERO** 🤔"
        kolor = 0xffe600

    embed = discord.Embed(title="📊 STATYSTYKI HAZARDOWE GRACZA", color=kolor)
    embed.add_field(name="🔴 Łącznie przegrano:", value=tekst_lost, inline=False)
    embed.add_field(name="🟢 Łącznie wygrano:", value=tekst_win, inline=False)
    embed.add_field(name="───────────────────", value=status, inline=False)
    embed.add_field(name="Wynik końcowy:", value=tekst_bilans, inline=False)
    embed.set_footer(text="Wiadomość zniknie automatycznie za 10 sekund...")

    odpowiedz = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=10)
    except: pass
    await odpowiedz.delete(delay=10)

@bot.command()
async def topfrajerzy(ctx):
    data = load_data()
    ranking = []
    
    for user_name, dane in data.items():
        if isinstance(dane, dict) and ("divines" in dane or "mirrors" in dane):
            divs = dane.get("divines", 0)
            mirrors = dane.get("mirrors", 0)
            if divs > 0 or mirrors > 0:
                ranking.append((user_name, mirrors, divs))
                
    if not ranking:
        await ctx.send("🕊️ Na serwerze nie ma jeszcze żadnych frajerów!")
        return
        
    ranking.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    wyglad_rankingu = "🏆 **RANKING NAJWIĘKSZYCH FRAJERÓW SERWERA:**\n"
    for miejsce, (u_name, mirrors, divs) in enumerate(ranking[:10], start=1):
        straty_tekst = ""
        if mirrors > 0: straty_tekst += f"`{mirrors} Mirrorów`"
        if divs > 0:
            if straty_tekst: straty_tekst += " i "
            straty_tekst += f"`{divs} Divine'ów`"
        wyglad_rankingu += f"{miejsce}. **{u_name}** — przegrane: {straty_tekst}\n"
        
    await ctx.send(wyglad_rankingu)

@bot.command()
async def gambling(ctx, *, wiadomosc: str):
    liczba_str = "".join(filter(str.isdigit, wiadomosc))
    
    if not liczba_str:
        blad = await ctx.send(f"❌ {ctx.author.mention}, musisz podać liczbę! Np. `!gambling 6`")
        try: await ctx.message.delete(delay=5)
        except: pass
        await blad.delete(delay=5)
        return

    ilosc = int(liczba_str)
    
    if ilosc <= 0:
        blad = await ctx.send(f"❌ {ctx.author.mention}, liczba musi być większa od 0!")
        try: await ctx.message.delete(delay=5)
        except: pass
        await blad.delete(delay=5)
        return

    if ilosc == 1:
        nazwa_waluty = "Karta"
    elif ilosc in [2, 3, 4] or (ilosc > 20 and ilosc % 10 in [2, 3, 4] and ilosc % 100 not in [12, 13, 14]):
        nazwa_waluty = "Karty"
    else:
        nazwa_waluty = "Kart"

    opcje = ["podwojenie", "spalenie", "zostaje", "modyfikacja"]
    wynik = random.choice(opcje)

    if wynik == "podwojenie":
        nowa_ilosc = ilosc * 2
        embed = discord.Embed(
            title="🎰 GAMBLING: 🎉 PODWOJENIE! 🎉",
            description=f"{ctx.author.mention} wrzuca **{ilosc} {nazwa_waluty}** do urządzenia...\n\n🔥 **WYNIK: {nowa_ilosc}**\nNiebieska energia błysnęła jasnym światłem!",
            color=0x00ff87
        )
    elif wynik == "spalenie":
        embed = discord.Embed(
            title="🎰 GAMBLING: 💀 SPALONE DO ZERA! 💀",
            description=f"{ctx.author.mention} wrzuca **{ilosc} {nazwa_waluty}** do urządzenia...\n\n🔥 **WYNIK: 0**\nUps... Wszystko zniknęło!",
            color=0xff4f4f
        )
    elif wynik == "zostaje":
        embed = discord.Embed(
            title="🎰 GAMBLING: ⚖️ NIC SIĘ NIE ZMIENIŁO ⚖️",
            description=f"{ctx.author.mention} wrzuca **{ilosc} {nazwa_waluty}** do urządzenia...\n\n🔥 **WYNIK: {ilosc}**\nKarty zawirowały i wróciły w tej samej ilości.",
            color=0xffe600
        )
    else:
        nowa_ilosc = random.randint(1, ilosc + 2)
        while nowa_ilosc in [0, ilosc, ilosc * 2]:
            nowa_ilosc = random.randint(1, ilosc + 2)
            
        embed = discord.Embed(
            title="🎰 GAMBLING: 🌀 ZMODYFIKOWANO ILOŚĆ! 🌀",
            description=f"{ctx.author.mention} wrzuca **{ilosc} {nazwa_waluty}** do urządzenia...\n\n🔥 **WYNIK: {nowa_ilosc}**\nLiczba kart ulega zmianie!",
            color=0xffa500
        )

    embed.set_footer(text="To jest czysty symulator. Wynik nie wpływa na bazę. Zniknie za 10s...")
    odpowiedz = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=10)
    except: pass
    await odpowiedz.delete(delay=10)

@bot.command()
async def pomoc(ctx):
    embed = discord.Embed(title="🎰 CENTRUM HAZARDU 🎰", color=0x00ff87)
    embed.add_field(name="📉 `!lost <kwota>`", value="Zapisuje straty do bazy.", inline=False)
    embed.add_field(name="📈 `!win <kwota>`", value="Zapisuje wygrane do bazy.", inline=False)
    embed.add_field(name="📊 `!stats`", value="Wyświetla Twój oficjalny bilans.", inline=False)
    embed.add_field(name="🏆 `!topfrajerzy`", value="Ranking bankrutów.", inline=False)
    embed.add_field(name="🎰 `!gambling <ilość>`", value="Symulator kart z Harvesta.", inline=False)
    embed.add_field(name="🧹 `!clear <ilość/all>`", value="Czyszczenie kanału.", inline=False)
    
    odpowiedz = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=5)
    except: pass
    await odpowiedz.delete(delay=5)
bot.run(TOKEN)