import os
import discord
from discord import app_commands
import aiohttp
import asyncio

INTENTS = discord.Intents.default()
CLIENT = discord.Client(intents=INTENTS)
TREE = app_commands.CommandTree(CLIENT)

DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN ")

QB_URL = os.getenv("QB_URL")
QB_USER = os.getenv("QB_USER")
QB_PASS = os.getenv("QB_PASS")

RADARR_URL = os.getenv("RADARR_URL")
RADARR_KEY = os.getenv("RADARR_KEY")

SONARR_URL = os.getenv("SONARR_URL")
SONARR_KEY = os.getenv("SONARR_KEY")



# ======================================================
# =============== QBITTORRENT HELPERS ==================
# ======================================================
async def qb_login(session):
    payload = {"username": QB_USER, "password": QB_PASS}
    await session.post(f"{QB_URL}/api/v2/auth/login", data=payload)


async def qb_add_torrent(session, magnet, category, rename=None):
    data = {"urls": magnet, "category": category}

    if rename:
        data["rename"] = rename

    await session.post(f"{QB_URL}/api/v2/torrents/add", data=data)


# ======================================================
# ================= RADARR HELPERS =====================
# ======================================================
async def radarr_add_unmonitored(session, imdb_id):
    if not imdb_id:
        return

    params = {"apikey": RADARR_KEY}
    payload = {
        "imdbId": imdb_id,
        "monitored": False
    }

    await session.post(f"{RADARR_URL}/api/v3/movie", params=params, json=payload)


# ======================================================
# ================= SONARR HELPERS =====================
# ======================================================
async def sonarr_add_unmonitored(session, imdb_id):
    if not imdb_id:
        return

    params = {"apikey": SONARR_KEY}
    payload = {
        "imdbId": imdb_id,
        "monitored": False
    }

    await session.post(f"{SONARR_URL}/api/v3/series", params=params, json=payload)


# ======================================================
# ================= DISCORD COMMANDS ===================
# ======================================================

@TREE.command(name="magnet_movie", description="Add magnet to Radarr + qBittorrent")
@app_commands.describe(
    magnet="Magnet link",
    name="Optional rename for torrent",
    imdb_id="Optional IMDB ID"
)
async def magnet_movie(interaction, magnet: str, name: str | None = None, imdb_id: str | None = None):
    print(f"G.ID {DISCORD_GUILD_ID}")
    print(f"G.ID {interaction.guild_id}")
    if interaction.guild_id != DISCORD_GUILD_ID:
        return await interaction.response.send_message("Not allowed here.", ephemeral=True)

    async with aiohttp.ClientSession() as session:
        await radarr_add_unmonitored(session, imdb_id)
        await qb_login(session)
        await qb_add_torrent(session, magnet, "radarr", name)

    await interaction.response.send_message("🎬 Movie magnet processed!")


@TREE.command(name="magnet_series", description="Add magnet to Sonarr + qBittorrent")
@app_commands.describe(
    magnet="Magnet link",
    name="Optional rename for torrent",
    imdb_id="Optional IMDB ID"
)
async def magnet_series(interaction, magnet: str, name: str | None = None, imdb_id: str | None = None):
    print(f"G.ID {DISCORD_GUILD_ID}")
    print(f"G.ID {interaction.guild_id}")
    if interaction.guild_id != DISCORD_GUILD_ID:
        return await interaction.response.send_message("Not allowed here.", ephemeral=True)

    async with aiohttp.ClientSession() as session:
        await sonarr_add_unmonitored(session, imdb_id)
        await qb_login(session)
        await qb_add_torrent(session, magnet, "sonarr", name)

    await interaction.response.send_message("📺 Series magnet processed!")


@TREE.command(name="help_magnets", description="Explain bot commands")
async def help_magnets(interaction):

    text = """
**Magnet Bot Help**

`/magnet_movie`
→ Sends magnet to Radarr + qBittorrent
Arguments:
• magnet (required)
• name (optional)
• imdb_id (optional)

`/magnet_series`
→ Sends magnet to Sonarr + qBittorrent
Arguments:
• magnet (required)
• name (optional)
• imdb_id (optional)
"""
    await interaction.response.send_message(text)


# ======================================================
# ================= BOT STARTUP ========================
# ======================================================

@CLIENT.event
async def on_ready():
    try:
        guild = discord.Object(id=DISCORD_GUILD_ID)
        synced = await TREE.sync()
        print(f"Bot logged in as {CLIENT.user}")
        print(f"synced {len(synced)} command to guild {guild.id}")

    except Exception as e:
        print(f"error syncing commands {e}")

CLIENT.run(DISCORD_TOKEN)

