import discord
from discord.ext import commands
import json
import os
import random
from aiohttp import web
import aiohttp
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DATA_FILE = "data.json"
BOT_FOLDER = "bot page"

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
    path = os.path.join(BOT_FOLDER, "index.html")
    if os.path.exists(path):
        return web.FileResponse(path)
    return web.Response(text=f"Missing index.html in folder '{BOT_FOLDER}'!", status=404)

async def handle_css(request):
    path = os.path.join(BOT_FOLDER, "style.css")
    if os.path.exists(path):
        return web.FileResponse(path)
    return web.Response(text=f"Missing style.css in folder '{BOT_FOLDER}'!", status=404)

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
    app.router.add_static('/', path=r"C:\Users\xyziu\Desktop\discord_bot\bot page", show_index=False)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("🌐 Web server started at http://localhost:8000")

@bot.event
async def on_ready():
    print(f"🤖 Logged in successfully as {bot.user.name}")
    print(f"📂 Database {DATA_FILE} is ready.")
    bot.loop.create_task(start_web_server())


# ── CLEAR ──────────────────────────────────────────────────────────────────────

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, argument: str):
    if argument.lower() == "all":
        deleted = await ctx.channel.purge(limit=None)
        count = len(deleted)
        msg = await ctx.send(f"✨ Channel completely cleared! ({count} messages deleted)")
        await msg.delete(delay=15)
        return
    try:
        amount = int(argument)
        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"🧹 Deleted {amount} messages!")
        await msg.delete(delay=15)
    except ValueError:
        await ctx.send(f"❌ {ctx.author.mention}, invalid argument! Enter a number (e.g. `!clear 10`) or `!clear all`.")

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ {ctx.author.mention}, you don't have permission to manage messages!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ {ctx.author.mention}, you must provide a number or `all`! E.g. `!clear 10`")


# ── LOST ───────────────────────────────────────────────────────────────────────

@bot.command()
async def lost(ctx, *, message: str):
    data = load_data()
    user_name = str(ctx.author.name)
    parts = message.lower().replace("and", " ").replace("+", " ").split()

    added_divines = 0
    added_mirrors = 0
    found_currency = False

    for part in parts:
        num_str = "".join(filter(str.isdigit, part))
        if len(num_str) > 0:
            num = int(num_str)
            if part.endswith("m"):
                added_mirrors += num
                found_currency = True
            elif part.endswith("d") or (part == parts[-1] and len(parts) == 1):
                added_divines += num
                found_currency = True

    if not found_currency:
        err = await ctx.send(f"❌ {ctx.author.mention}, I didn't understand the amount! Use e.g. `1M and 200d`, `200d` or `1M`.")
        try: await ctx.message.delete(delay=15)
        except: pass
        await err.delete(delay=15)
        return

    if user_name not in data or not isinstance(data[user_name], dict):
        data[user_name] = {"divines": 0, "mirrors": 0, "win_divines": 0, "win_mirrors": 0}

    data[user_name]["avatar_url"] = str(ctx.author.display_avatar.url)
    if "divines" not in data[user_name]: data[user_name]["divines"] = 0
    if "mirrors" not in data[user_name]: data[user_name]["mirrors"] = 0
    if "win_divines" not in data[user_name]: data[user_name]["win_divines"] = 0
    if "win_mirrors" not in data[user_name]: data[user_name]["win_mirrors"] = 0

    data[user_name]["divines"] += added_divines
    data[user_name]["mirrors"] += added_mirrors
    save_data(data)

    lost_items = []
    if added_mirrors > 0: lost_items.append(f"**{added_mirrors} Mirrors**")
    if added_divines > 0: lost_items.append(f"**{added_divines} Divines**")
    lost_text = " and ".join(lost_items)

    balance = f"`{data[user_name]['divines']} Divines`"
    if data[user_name]["mirrors"] > 0:
        balance = f"`{data[user_name]['mirrors']} Mirrors` and " + balance

    embed = discord.Embed(
        title="📉 LOSS RECORDED",
        description=f"unlucky {ctx.author.mention} XDDD\nYou just lost {lost_text}.",
        color=0xff4f4f
    )
    embed.add_field(name="🔴 Your total losses are now:", value=balance, inline=False)
    embed.set_footer(text="Message will disappear automatically in 10 seconds...")

    reply = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)


# ── WIN ────────────────────────────────────────────────────────────────────────

@bot.command()
async def win(ctx, *, message: str):
    data = load_data()
    user_name = str(ctx.author.name)
    parts = message.lower().replace("and", " ").replace("+", " ").split()

    added_divines = 0
    added_mirrors = 0
    found_currency = False

    for part in parts:
        num_str = "".join(filter(str.isdigit, part))
        if len(num_str) > 0:
            num = int(num_str)
            if part.endswith("m"):
                added_mirrors += num
                found_currency = True
            elif part.endswith("d") or (part == parts[-1] and len(parts) == 1):
                added_divines += num
                found_currency = True

    if not found_currency:
        err = await ctx.send(f"❌ {ctx.author.mention}, I didn't understand the amount! Use e.g. `200d` or `1M`.")
        try: await ctx.message.delete(delay=15)
        except: pass
        await err.delete(delay=15)
        return

    if user_name not in data or not isinstance(data[user_name], dict):
        data[user_name] = {"divines": 0, "mirrors": 0, "win_divines": 0, "win_mirrors": 0}

    data[user_name]["avatar_url"] = str(ctx.author.display_avatar.url)
    if "divines" not in data[user_name]: data[user_name]["divines"] = 0
    if "mirrors" not in data[user_name]: data[user_name]["mirrors"] = 0
    if "win_divines" not in data[user_name]: data[user_name]["win_divines"] = 0
    if "win_mirrors" not in data[user_name]: data[user_name]["win_mirrors"] = 0

    data[user_name]["win_divines"] += added_divines
    data[user_name]["win_mirrors"] += added_mirrors
    save_data(data)

    won_items = []
    if added_mirrors > 0: won_items.append(f"**{added_mirrors} Mirrors**")
    if added_divines > 0: won_items.append(f"**{added_divines} Divines**")
    won_text = " and ".join(won_items)

    win_balance = f"`{data[user_name]['win_divines']} Divines`"
    if data[user_name]["win_mirrors"] > 0:
        win_balance = f"`{data[user_name]['win_mirrors']} Mirrors` and " + win_balance

    embed = discord.Embed(
        title="📈 WIN RECORDED",
        description=f"GG {ctx.author.mention}! Someone's on a lucky streak XDDD\nYou just gained {won_text}.",
        color=0x00ff87
    )
    embed.add_field(name="🟢 Your total winnings are now:", value=win_balance, inline=False)
    embed.set_footer(text="Message will disappear automatically in 10 seconds...")

    reply = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)


# ── STATS ──────────────────────────────────────────────────────────────────────

@bot.command()
async def stats(ctx):
    data = load_data()
    user_name = str(ctx.author.name)

    if user_name not in data or not isinstance(data[user_name], dict):
        err = await ctx.send(f"🕊️ {ctx.author.mention}, your account is clean!")
        try: await ctx.message.delete(delay=15)
        except: pass
        await err.delete(delay=15)
        return

    lost_divs = data[user_name].get("divines", 0)
    lost_mirrors = data[user_name].get("mirrors", 0)
    win_divs = data[user_name].get("win_divines", 0)
    win_mirrors = data[user_name].get("win_mirrors", 0)

    if lost_divs == 0 and lost_mirrors == 0 and win_divs == 0 and win_mirrors == 0:
        err = await ctx.send(f"🕊️ {ctx.author.mention}, no gambling activity recorded.")
        try: await ctx.message.delete(delay=15)
        except: pass
        await err.delete(delay=15)
        return

    bal_divs = win_divs - lost_divs
    bal_mirrors = win_mirrors - lost_mirrors

    text_lost = f"`{lost_divs} Divines`"
    if lost_mirrors > 0: text_lost = f"`{lost_mirrors} Mirrors` and " + text_lost

    text_win = f"`{win_divs} Divines`"
    if win_mirrors > 0: text_win = f"`{win_mirrors} Mirrors` and " + text_win

    text_balance = ""
    if bal_mirrors > 0: text_balance += f"`+{bal_mirrors} Mirrors` "
    elif bal_mirrors < 0: text_balance += f"`{bal_mirrors} Mirrors` "
    if bal_divs > 0: text_balance += f"`+{bal_divs} Divines`"
    elif bal_divs < 0: text_balance += f"`{bal_divs} Divines`"
    elif bal_divs == 0 and text_balance == "": text_balance += "`0 Divines`"

    if bal_mirrors > 0 or (bal_mirrors == 0 and bal_divs > 0):
        status = "📈 **OVERALL BALANCE: PROFIT** 🤑"
        color = 0x00ff87
    elif bal_mirrors < 0 or (bal_mirrors == 0 and bal_divs < 0):
        status = "📉 **OVERALL BALANCE: LOSS** 💀 (Total loser XDDD)"
        color = 0xff4f4f
    else:
        status = "⚖️ **OVERALL BALANCE: BREAK EVEN** 🤔"
        color = 0xffe600

    embed = discord.Embed(title="📊 PLAYER GAMBLING STATS", color=color)
    embed.add_field(name="🔴 Total lost:", value=text_lost, inline=False)
    embed.add_field(name="🟢 Total won:", value=text_win, inline=False)
    embed.add_field(name="───────────────────", value=status, inline=False)
    embed.add_field(name="Final result:", value=text_balance, inline=False)
    embed.set_footer(text="Message will disappear automatically in 10 seconds...")

    reply = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)


# ── TOP LOSERS ─────────────────────────────────────────────────────────────────

@bot.command()
async def toplosers(ctx):
    data = load_data()
    ranking = []

    for user_name, info in data.items():
        if isinstance(info, dict) and ("divines" in info or "mirrors" in info):
            divs = info.get("divines", 0)
            mirrors = info.get("mirrors", 0)
            if divs > 0 or mirrors > 0:
                ranking.append((user_name, mirrors, divs))

    if not ranking:
        await ctx.send("🕊️ No losers on this server yet!")
        return

    ranking.sort(key=lambda x: (x[1], x[2]), reverse=True)

    ranking_text = "🏆 **TOP LOSERS RANKING:**\n"
    for place, (u_name, mirrors, divs) in enumerate(ranking[:10], start=1):
        loss_text = ""
        if mirrors > 0: loss_text += f"`{mirrors} Mirrors`"
        if divs > 0:
            if loss_text: loss_text += " and "
            loss_text += f"`{divs} Divines`"
        ranking_text += f"{place}. **{u_name}** — lost: {loss_text}\n"

    await ctx.send(ranking_text)


# ── GAMBLING ───────────────────────────────────────────────────────────────────

@bot.command()
async def gambling(ctx, *, message: str):
    num_str = "".join(filter(str.isdigit, message))

    if not num_str:
        err = await ctx.send(f"❌ {ctx.author.mention}, you must provide a number! E.g. `!gambling 6`")
        try: await ctx.message.delete(delay=15)
        except: pass
        await err.delete(delay=15)
        return

    amount = int(num_str)

    if amount <= 0:
        err = await ctx.send(f"❌ {ctx.author.mention}, number must be greater than 0!")
        try: await ctx.message.delete(delay=15)
        except: pass
        await err.delete(delay=15)
        return

    card_word = "Card" if amount == 1 else "Cards"
    options = ["double", "burn", "unchanged", "modified"]
    result = random.choice(options)

    if result == "double":
        new_amount = amount * 2
        embed = discord.Embed(
            title="🎰 GAMBLING: 🎉 DOUBLED! 🎉",
            description=f"{ctx.author.mention} throws **{amount} {card_word}** into the device...\n\n🔥 **RESULT: {new_amount}**\nBlue energy flashed with a bright light!",
            color=0x00ff87
        )
    elif result == "burn":
        embed = discord.Embed(
            title="🎰 GAMBLING: 💀 BURNED TO ZERO! 💀",
            description=f"{ctx.author.mention} throws **{amount} {card_word}** into the device...\n\n🔥 **RESULT: 0**\nOops... Everything vanished!",
            color=0xff4f4f
        )
    elif result == "unchanged":
        embed = discord.Embed(
            title="🎰 GAMBLING: ⚖️ NOTHING CHANGED ⚖️",
            description=f"{ctx.author.mention} throws **{amount} {card_word}** into the device...\n\n🔥 **RESULT: {amount}**\nThe cards swirled and returned in the same amount.",
            color=0xffe600
        )
    else:
        new_amount = random.randint(1, amount + 2)
        while new_amount in [0, amount, amount * 2]:
            new_amount = random.randint(1, amount + 2)
        embed = discord.Embed(
            title="🎰 GAMBLING: 🌀 AMOUNT MODIFIED! 🌀",
            description=f"{ctx.author.mention} throws **{amount} {card_word}** into the device...\n\n🔥 **RESULT: {new_amount}**\nThe number of cards has changed!",
            color=0xffa500
        )

    embed.set_footer(text="This is a pure simulator. Result does not affect the database. Disappears in 10s...")
    reply = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)


# ── BUILDS ─────────────────────────────────────────────────────────────────────

@bot.command()
async def setbuild(ctx, *, content: str):
    data = load_data()
    user_name = str(ctx.author.name)

    # Split on | to get optional description
    parts = content.split("|", 1)
    link = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else None

    if not link.startswith("http"):
        err = await ctx.send(f"❌ {ctx.author.mention}, provide a valid link! E.g. `!setbuild https://poe.ninja/... | My OP boss killer`")
        try: await ctx.message.delete(delay=15)
        except: pass
        await err.delete(delay=15)
        return

    if user_name not in data or not isinstance(data[user_name], dict):
        data[user_name] = {"divines": 0, "mirrors": 0, "win_divines": 0, "win_mirrors": 0}

    data[user_name]["build_link"] = link
    data[user_name]["build_desc"] = description
    data[user_name]["avatar_url"] = str(ctx.author.display_avatar.url)
    save_data(data)

    embed = discord.Embed(
        title="⚔️ BUILD SAVED",
        description=f"{ctx.author.mention} updated their build!",
        color=0x00d2ff
    )
    embed.add_field(name="🔗 Link", value=link, inline=False)
    if description:
        embed.add_field(name="📝 Description", value=description, inline=False)
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text="Message will disappear in 10 seconds...")

    reply = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)

@bot.command()
async def builds(ctx):
    data = load_data()
    players_with_builds = [
        (name, info) for name, info in data.items()
        if isinstance(info, dict) and "build_link" in info
    ]

    if not players_with_builds:
        err = await ctx.send("🕊️ Nobody has saved a build yet! Use `!setbuild <link>`")
        await err.delete(delay=15)
        return

    embed = discord.Embed(
        title="⚔️ PLAYER BUILDS",
        description="Click a link to view someone's build:",
        color=0x00d2ff
    )

    for name, info in players_with_builds:
        link = info["build_link"]
        desc = info.get("build_desc")
        field_value = f"[🔗 View build]({link})"
        if desc:
            field_value += f"\n*{desc}*"
        embed.add_field(
            name=f"👤 {name}",
            value=field_value,
            inline=True
        )

    embed.set_footer(text="Use !setbuild <link> to add your build.")
    await ctx.send(embed=embed)

@bot.command()
async def delbuild(ctx):
    data = load_data()
    user_name = str(ctx.author.name)

    if user_name not in data or "build_link" not in data.get(user_name, {}):
        err = await ctx.send(f"❌ {ctx.author.mention}, you don't have a saved build!")
        try: await ctx.message.delete(delay=15)
        except: pass
        await err.delete(delay=15)
        return

    del data[user_name]["build_link"]
    save_data(data)

    reply = await ctx.send(f"🗑️ {ctx.author.mention}, your build has been deleted.")
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)


# ── POE.NINJA PRICES ───────────────────────────────────────────────────────────

LEAGUE = "Mirage"  # Update this when the league changes

# poe.ninja API — correct endpoint discovered via browser network inspection
# Format: https://poe.ninja/poe1/api/economy/exchange/current/overview?league=LEAGUE&type=TYPE
POE_NINJA_TYPES = {
    "cards": "DivinationCard",
}
POE_NINJA_BASE = "https://poe.ninja/poe1/api/economy/exchange/current/overview"

async def fetch_poe_ninja(category: str, top: int = 5):
    """Fetches top N most expensive items from poe.ninja using the correct API endpoint."""
    item_type = POE_NINJA_TYPES[category]
    params = {"league": LEAGUE, "type": item_type}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://poe.ninja/poe1/economy/{LEAGUE.lower()}/divination-cards",
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(POE_NINJA_BASE, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                print(f"[poe.ninja] GET {resp.url} -> {resp.status}")
                if resp.status != 200:
                    text = await resp.text()
                    print(f"[poe.ninja] Error response (first 300 chars): {text[:300]}")
                    return None
                data = await resp.json(content_type=None)
    except Exception as e:
        print(f"[poe.ninja] Exception: {e}")
        return None

    # new API uses "items" + "lines" structure — items have names, lines have prices by id
    items_map = {item["id"]: item.get("name", "?") for item in data.get("items", [])}
    raw_lines = data.get("lines", [])

    if not raw_lines:
        # fallback: maybe it's the old structure with name directly in lines
        raw_lines = data.get("lines", [])
        print(f"[poe.ninja] Keys in response: {list(data.keys())}, lines count: {len(raw_lines)}")
        if not raw_lines:
            return None

    # detect which structure we got
    if raw_lines and "chaosValue" in raw_lines[0]:
        # old structure: name + chaosValue directly in line
        lines_sorted = sorted(raw_lines, key=lambda x: x.get("chaosValue", 0), reverse=True)
        return [
            {
                "name":   item.get("name", "?"),
                "chaos":  round(item.get("chaosValue", 0), 1),
                "divine": round(item.get("divineValue", 0), 2),
            }
            for item in lines_sorted[:top]
        ]
    elif raw_lines and "chaosEquivalent" in raw_lines[0]:
        # currency structure
        lines_sorted = sorted(raw_lines, key=lambda x: x.get("chaosEquivalent", 0), reverse=True)
        return [
            {
                "name":   item.get("currencyTypeName", item.get("name", "?")),
                "chaos":  round(item.get("chaosEquivalent", 0), 1),
                "divine": round(item.get("chaosEquivalent", 0) / 200, 2),
            }
            for item in lines_sorted[:top]
        ]
    else:
        # new structure: lines reference items by id, prices in "primaryValue"
        print(f"[poe.ninja] New structure detected. Sample line keys: {list(raw_lines[0].keys()) if raw_lines else 'empty'}")
        lines_sorted = sorted(raw_lines, key=lambda x: x.get("primaryValue", x.get("chaosValue", 0)), reverse=True)
        result = []
        for item in lines_sorted[:top]:
            item_id = item.get("itemId", item.get("id", None))
            name = items_map.get(item_id, item.get("name", "?"))
            chaos = round(item.get("primaryValue", item.get("chaosValue", 0)), 1)
            divine = round(item.get("secondaryValue", item.get("divineValue", chaos / 200)), 2)
            result.append({"name": name, "chaos": chaos, "divine": divine})
        return result

MEDALS = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

# ── CARDS ──────────────────────────────────────────────────────────────────────

@bot.command()
async def cards(ctx):
    """Top 5 most expensive Divination Cards from poe.ninja"""
    async with ctx.typing():
        items = await fetch_poe_ninja("cards")

    if items is None:
        err = await ctx.send("❌ Failed to fetch data from poe.ninja. Try again later.")
        await err.delete(delay=15)
        return

    embed = discord.Embed(
        title=f"🃏 TOP 5 DIVINATION CARDS — {LEAGUE}",
        description=f"Live data from [poe.ninja](https://poe.ninja/poe1/economy/{LEAGUE.lower()}/divination-cards)",
        color=0xc8a951
    )
    for i, item in enumerate(items):
        embed.add_field(
            name=f"{MEDALS[i]} {item['name']}",
            value=f"`{item['chaos']}` chaos  •  `{item['divine']}` divine",
            inline=False
        )
    embed.set_footer(text=f"League: {LEAGUE} • Live prices")

    reply = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)


# ── CURRENCY PRICES ────────────────────────────────────────────────────────────

CURRENCY_WATCH = ["Divine Orb", "Mirror of Kalandra", "Hinekora's Lock", "Mirror Shard"]

@bot.command()
async def currency(ctx):
    """Shows prices of key currencies from poe.ninja"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://poe.ninja/poe1/economy/{LEAGUE.lower()}/currency",
    }
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    "https://poe.ninja/poe1/api/economy/exchange/current/overview",
                    params={"league": LEAGUE, "type": "Currency"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        raise Exception(f"HTTP {resp.status}")
                    data = await resp.json(content_type=None)
        except Exception as e:
            err = await ctx.send(f"❌ Failed to fetch data from poe.ninja: {e}")
            await err.delete(delay=15)
            return

    # new API: items[] has names, lines[] has prices, joined by id
    items_list = data.get("items", [])
    lines = data.get("lines", [])
    id_to_name = {item["id"]: item.get("name", "?") for item in items_list}
    by_name = {}
    for line in lines:
        item_id = line.get("itemId", line.get("id"))
        name = id_to_name.get(item_id, "")
        if name:
            by_name[name] = line

    ICONS = {
        "Divine Orb":         "🔱",
        "Mirror of Kalandra": "🪞",
        "Hinekora's Lock":    "🔒",
        "Mirror Shard":       "🔮",
    }

    embed = discord.Embed(
        title=f"💰 KEY CURRENCY PRICES — {LEAGUE}",
        description=f"Live data from [poe.ninja](https://poe.ninja/poe1/economy/{LEAGUE.lower()}/currency)",
        color=0xf0c040
    )

    divine_item = by_name.get("Divine Orb")
    divine_chaos = round(divine_item.get("primaryValue", 1), 1) if divine_item else 1

    for name in CURRENCY_WATCH:
        item = by_name.get(name)
        icon = ICONS.get(name, "•")
        if item:
            chaos = round(item.get("primaryValue", 0), 1)
            if name == "Divine Orb":
                value = f"`{chaos:,}` chaos"
            else:
                divine_val = round(chaos / divine_chaos, 2) if divine_chaos else 0
                value = f"`{divine_val}` divine"
            embed.add_field(name=f"{icon} {name}", value=value, inline=False)
        else:
            embed.add_field(name=f"{icon} {name}", value="`— no data —`", inline=False)

    embed.set_footer(text=f"League: {LEAGUE} • Live prices")
    reply = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)


# ── VENDOR RECIPES ─────────────────────────────────────────────────────────────

VENDOR_RECIPES = {
    "💰 Currency": [
        ("Chromatic Orb",      "Item with R+G+B linked sockets → vendor"),
        ("Orb of Fusing",      "4x Jeweller's Orb → vendor"),
        ("Jeweller's Orb",     "2x Orb of Alteration → vendor"),
        ("Orb of Alteration",  "4x Orb of Augmentation → vendor"),
        ("Orb of Augmentation","4x Orb of Transmutation → vendor"),
        ("Orb of Chance",      "Full set of magic items (unid, 60–74) → vendor"),
        ("Regal Orb",          "Full set of rare items (unid, 75+) → vendor"),
        ("Chaos Orb",          "Full set of rare items (unid, 60–74) → vendor"),
        ("Exalted Shard x2",   "Full set of rare items (id, 75+) → vendor"),
        ("Divine Orb",         "6x Sacrifice at Midnight → vendor"),
        ("Orb of Scouring",    "2x Orb of Regret → vendor"),
        ("Orb of Regret",      "5x Orb of Scouring → vendor"),
        ("Blessed Orb",        "6x Orb of Chance → vendor"),
        ("Vaal Orb",           "7x Vaal Skill Gem + 1 Sacrifice at Dusk → vendor"),
        ("Orb of Binding",     "Full set of items (normal, any level) → vendor"),
    ],
    "⚗️ Flasks": [
        ("Life Flask (upgrade)", "3x same level life flask → vendor (next tier)"),
        ("Mana Flask (upgrade)", "3x same level mana flask → vendor (next tier)"),
        ("Hybrid Flask",         "1x Life Flask + 1x Mana Flask (same tier) → vendor"),
        ("Quicksilver Flask",    "1x Quicksilver Flask + Battered Folio → vendor"),
        ("Gold Flask",           "1x Quicksilver Flask + Orb of Chance → vendor"),
    ],
    "💎 Gems": [
        ("Level 1 Gem (any)",    "Gem + Orb of Regret → vendor (resets XP)"),
        ("Empower Support",      "Gem + Orb of Alteration → vendor (chance)"),
        ("Enhance Support",      "Gem + Orb of Augmentation → vendor (chance)"),
        ("Enlighten Support",    "3x Skill Gems (same name, 20 quality each) → vendor"),
        ("20% Quality Gem",      "Gem + Gemcutter's Prism → vendor (resets to 20%)"),
    ],
    "🔨 Equipment": [
        ("6-socket item",        "7x Jeweller's Orb → vendor any item for 6 sockets"),
        ("6-link item",          "350x Orb of Fusing → vendor any item for 6-link"),
        ("20% Quality weapon",   "Weapon + Blacksmith's Whetstone(s) → vendor (to 20%)"),
        ("20% Quality armour",   "Armour + Armourer's Scrap(s) → vendor (to 20%)"),
        ("Rare item (ilvl 60+)", "Any 2h weapon + 3 rare rings → vendor (chance at rare)"),
        ("Mirrored item shard",  "Sell any mirrored item → vendor (gets shards)"),
    ],
    "🗺️ Maps": [
        ("3 same maps → 1 higher", "3x same Tier map → vendor (next tier map)"),
        ("Sacrifice Fragments",    "4x same Sacrifice Fragment → vendor (next tier)"),
        ("Offering to the Goddess","3x same map (corrupted) → vendor (unique map chance)"),
        ("Elder/Shaper map",       "3x same influenced map → vendor (same influenced)"),
    ],
}

VENDOR_CATEGORIES = list(VENDOR_RECIPES.keys())

class VendorView(discord.ui.View):
    def __init__(self, author_id: int, message=None):
        super().__init__(timeout=15)
        self.author_id = author_id
        self.message = message
        self.page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.clear_items()
        for i, cat in enumerate(VENDOR_CATEGORIES):
            btn = discord.ui.Button(
                label=cat,
                style=discord.ButtonStyle.primary if i == self.page else discord.ButtonStyle.secondary,
                custom_id=str(i)
            )
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, index: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("❌ Only the command author can use these buttons!", ephemeral=True)
                return
            self.page = index
            self._update_buttons()
            await interaction.response.edit_message(embed=self._build_embed(), view=self)
        return callback

    def _build_embed(self) -> discord.Embed:
        cat = VENDOR_CATEGORIES[self.page]
        recipes = VENDOR_RECIPES[cat]
        embed = discord.Embed(
            title=f"📦 VENDOR RECIPES — {cat}",
            description="Click a category button to switch.",
            color=0xe8b84b
        )
        for name, recipe in recipes:
            embed.add_field(name=f"➤ {name}", value=recipe, inline=False)
        embed.set_footer(text=f"Page {self.page + 1}/{len(VENDOR_CATEGORIES)} • Disappears in 15s")
        return embed

    async def on_timeout(self):
        try:
            await self.message.delete()
        except:
            pass


@bot.command()
async def vendor(ctx):
    """Vendor recipes with category buttons"""
    view = VendorView(author_id=ctx.author.id)
    embed = view._build_embed()
    reply = await ctx.send(embed=embed, view=view)
    view.message = reply
    try: await ctx.message.delete(delay=15)
    except: pass


# ── HELP ───────────────────────────────────────────────────────────────────────

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎰 GAMBLING CENTER 🎰", color=0x00ff87)
    embed.add_field(name="📉 `!lost <amount>`",    value="Records losses to the database.", inline=False)
    embed.add_field(name="📈 `!win <amount>`",      value="Records wins to the database.", inline=False)
    embed.add_field(name="📊 `!stats`",             value="Displays your official balance.", inline=False)
    embed.add_field(name="🏆 `!toplosers`",         value="Ranking of the biggest losers.", inline=False)
    embed.add_field(name="🎰 `!gambling <amount>`", value="Harvest card simulator.", inline=False)
    embed.add_field(name="─────────── POE TOOLS ───────────", value="​", inline=False)
    embed.add_field(name="🃏 `!cards`",             value=f"Top 5 most expensive Divination Cards ({LEAGUE}).", inline=False)
    embed.add_field(name="💰 `!currency`",          value="Live prices: Divine, Mirror, Hinekora's Lock, Mirror Shard.", inline=False)
    embed.add_field(name="📦 `!vendor`",            value="Vendor recipes — browse by category with buttons.", inline=False)
    embed.add_field(name="⚔️ `!setbuild <link>`",  value="Save your build link.", inline=False)
    embed.add_field(name="📋 `!builds`",            value="View all players' builds.", inline=False)
    embed.add_field(name="🗑️ `!delbuild`",         value="Delete your saved build.", inline=False)

    reply = await ctx.send(embed=embed)
    try: await ctx.message.delete(delay=15)
    except: pass
    await reply.delete(delay=15)


bot.run(TOKEN)