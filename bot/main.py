import os
import discord
from discord import app_commands
import requests

# -----------------------
# Environment Variables
# -----------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

QBITTORRENT_URL = os.getenv("QBITTORRENT_URL")
QBITTORRENT_USER = os.getenv("QBITTORRENT_USER")
QBITTORRENT_PASS = os.getenv("QBITTORRENT_PASS")

RADARR_URL = os.getenv("RADARR_URL")
RADARR_API_KEY = os.getenv("RADARR_API_KEY")

SONARR_URL = os.getenv("SONARR_URL")
SONARR_API_KEY = os.getenv("SONARR_API_KEY")

# -----------------------
# Discord Client
# -----------------------
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

GUILD = discord.Object(id=DISCORD_GUILD_ID)

# -----------------------
# qBittorrent Helpers
# -----------------------
def qb_login(session):
    session.post(
        f"{QBITTORRENT_URL}/api/v2/auth/login",
        data={"username": QBITTORRENT_USER, "password": QBITTORRENT_PASS},
        timeout=10,
    )

def qb_add_magnet(magnet, name=None, category=None):
    with requests.Session() as session:
        qb_login(session)
        payload = {
            "urls": magnet,
        }
        if name:
            payload["rename"] = name
        if category:
            payload["category"] = category

        session.post(
            f"{QBITTORRENT_URL}/api/v2/torrents/add",
            data=payload,
            timeout=10,
        )

# -----------------------
# Arr Helpers
# -----------------------
def notify_radarr(imdb_id):
    if not imdb_id:
        return

    requests.post(
        f"{RADARR_URL}/api/v3/movie",
        headers={"X-Api-Key": RADARR_API_KEY},
        json={
            "imdbId": imdb_id,
            "qualityProfileId": 1,
            "rootFolderPath": "/movies",
            "monitored": False,
            "addOptions": {"searchForMovie": True},
        },
        timeout=10,
    )

def notify_sonarr(imdb_id):
    if not imdb_id:
        return

    requests.post(
        f"{SONARR_URL}/api/v3/series",
        headers={"X-Api-Key": SONARR_API_KEY},
        json={
            "imdbId": imdb_id,
            "qualityProfileId": 1,
            "rootFolderPath": "/tv",
            "monitored": False,
            "addOptions": {"searchForMissingEpisodes": True},
        },
        timeout=10,
    )

# -----------------------
# Commands
# -----------------------
@tree.command(
    name="magnet_movie",
    description="Add a movie magnet (Radarr)",
    guild=GUILD,
)
@app_commands.describe(
    magnet="Magnet link",
    name="Optional torrent rename",
    imdb_id="Optional IMDb ID for Radarr",
)
async def magnet_movie(
    interaction: discord.Interaction,
    magnet: str,
    name: str | None = None,
    imdb_id: str | None = None,
):
    await interaction.response.defer(ephemeral=True)

    try:
        notify_radarr(imdb_id)
        qb_add_magnet(magnet, name=name, category="radarr")

        await interaction.followup.send(
            "✅ Movie magnet added successfully.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to add movie magnet:\n```{e}```",
            ephemeral=True,
        )

@tree.command(
    name="magnet_tv",
    description="Add a TV series magnet (Sonarr)",
    guild=GUILD,
)
@app_commands.describe(
    magnet="Magnet link",
    name="Optional torrent rename",
    imdb_id="Optional IMDb ID for Sonarr",
)
async def magnet_tv(
    interaction: discord.Interaction,
    magnet: str,
    name: str | None = None,
    imdb_id: str | None = None,
):
    await interaction.response.defer(ephemeral=True)

    try:
        notify_sonarr(imdb_id)
        qb_add_magnet(magnet, name=name, category="sonarr")

        await interaction.followup.send(
            "✅ TV series magnet added successfully.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(
            f"❌ Failed to add TV magnet:\n```{e}```",
            ephemeral=True,
        )

@tree.command(
    name="magnet_help",
    description="Show help for magnet commands",
    guild=GUILD,
)
async def magnet_help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📌 Magnetarr Commands",
        description="Use these commands to send magnet links to qBittorrent with Arr integration.",
        color=0x00BFFF,
    )

    embed.add_field(
        name="/magnet_movie",
        value=(
            "**Usage:**\n"
            "`/magnet_movie magnet:<link> [name] [imdb_id]`\n\n"
            "• Adds a movie magnet\n"
            "• Optional rename\n"
            "• Optional IMDb ID → Radarr"
        ),
        inline=False,
    )

    embed.add_field(
        name="/magnet_tv",
        value=(
            "**Usage:**\n"
            "`/magnet_tv magnet:<link> [name] [imdb_id]`\n\n"
            "• Adds a TV series magnet\n"
            "• Optional rename\n"
            "• Optional IMDb ID → Sonarr"
        ),
        inline=False,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# -----------------------
# Startup
# -----------------------
@client.event
async def on_ready():
    await tree.sync(guild=GUILD)
    print(f"✅ Logged in as {client.user}")

client.run(DISCORD_TOKEN)

