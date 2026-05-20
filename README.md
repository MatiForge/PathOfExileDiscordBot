# 🎰 PoE Gambling & Tools Discord Bot

A feature-rich Discord bot designed for **Path of Exile** players. It includes a complete gambling ledger system to track wins and losses (Divines/Mirrors), dynamic economy statistics fetched directly via the **poe.ninja API**, interactive UI components (buttons) for vendor recipes, and an integrated **aiohttp web server** that exposes data as a REST API.

---

## 🚀 Key Features

* **📊 Gambling Ledger:** Tracks individual server members' winnings, losses, and overall profit/loss standings using a local JSON database.
* **🏆 High-scores:** Dynamic leaderboard highlighting the biggest losers on the server (`!toplosers`).
* **💸 Live Economy Tracker:** Real-time data visualization for key currencies and the top 5 most expensive Divination Cards using the **poe.ninja API**.
* **📦 Interactive UI:** Clean Discord UI Buttons to seamlessly browse through extensive in-game Vendor Recipes.
* **⚔️ Build Showcasing:** Allows players to link, describe, list, and delete their Path of Exile build profiles.
* **🌐 Integrated Web Server:** Asynchronous background web server serving a frontend dashboard and exposing static endpoints for dynamic integration.

---

## 🎮 Bot Commands

### ────────── GAMBLING CENTER ──────────
* `!lost <amount>` – Records your gambling losses (e.g., `!lost 100d`, `!lost 1m and 50d`).
* `!win <amount>` – Records your gambling winnings (e.g., `!win 200d`, `!win 2m`).
* `!stats` – Displays your personal statistics, history, and calculated profit margin status.
* `!toplosers` – Prints a leaderboard showcasing the server's biggest losses.
* `!gambling <amount>` – A standalone, high-stakes Harvest card crafting simulator.

### ────────── POE TOOLS ──────────
* `!cards` – Lists the Top 5 most expensive Divination Cards in the current league.
* `!currency` – Shows real-time exchange rates for Mirror of Kalandra, Divine Orbs, Hinekora's Lock, and Mirror Shards.
* `!vendor` – Launches an interactive, button-based guide for currency, flask, gem, map, and equipment vendor recipes.
* `!setbuild <link> [| description]` – Saves your personal PoB or PoE.ninja build profile.
* `!builds` – Opens a catalog containing links to all registered players' character builds.
* `!delbuild` – Deletes your saved character build from the database.

### ────────── ADMIN & HELP ──────────
* `!clear <number/all>` – Utility tool to purge messages (requires `Manage Messages` permission).

### ────────── REQUIRED PACKAGES ──────────
* **pip install discord.py aiohttp python-dotenv**

### ────────── BOOT ──────────  
* **python bot.py**
