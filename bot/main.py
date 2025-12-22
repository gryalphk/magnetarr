import os
import re
import requests
import discord
from discord.ext import commands
from discord import app_commands
from asyncio import TimeoutError

MAGNET_RE = re.compile(r"magnet:\?xt=urn:btih:[a-zA-Z0-9]+")

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
QBIT_HOST = os.environ["QBIT_HOST"]
QBIT_USER = os.environ["QBIT_USER"]
QBIT_PASS = os.environ["QBIT_PASS"]

RADARR_HOST = os.environ["RADARR_HOST"]
RADARR_API_KEY = os.environ["RADARR_API_KEY"]
RADARR_ROOT_FOLDER = os.environ["RADARR_ROOT_FOLDER"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="magnet", description="Add a magnet link")
@app_commands.describe(
    link="Magnet link",
    name="Optional new name for the torrent (leave empty to keep original)"
)
async def magnet(
    interaction: discord.Interaction,
    link: str,
    name: str | None = None
):
    if not MAGNET_RE.match(link):
        await interaction.response.send_message("Invalid magnet link", ephemeral=True)
        return

    # Add directly with or without rename
    add_to_qbit(link, name)

    if name:
        add_to_radarr(name)
        await interaction.response.send_message(
            f"✅ Torrent added and renamed to **{name}**",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "✅ Torrent added with original name",
            ephemeral=True
        )

class RenameModal(discord.ui.Modal, title="Rename Torrent"):
    torrent_name = discord.ui.TextInput(
        label="New Torrent Name",
        placeholder="Enter the new torrent name",
        required=True,
        max_length=200
    )

    def __init__(self, magnet: str):
        super().__init__()
        self.magnet = magnet

    async def on_submit(self, interaction: discord.Interaction):
        new_name = self.torrent_name.value.strip()
        add_to_qbit(self.magnet, new_name)
        add_to_radarr(new_name)
        await interaction.response.send_message(
            f"✅ Added with renamed title: **{new_name}**",
            ephemeral=True
        )


class RenameView(discord.ui.View):
    def __init__(self, magnet: str):
        super().__init__(timeout=120)
        self.magnet = magnet

    def disable_all_buttons(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.primary)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons safely for ephemeral interaction
        self.disable_all_buttons()
        await interaction.response.edit_message(view=self)

        # Open modal AFTER editing the message
        await interaction.followup.send_modal(RenameModal(self.magnet))

    @discord.ui.button(label="Keep Name", style=discord.ButtonStyle.secondary)
    async def keep(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable buttons safely for ephemeral interaction
        self.disable_all_buttons()
        await interaction.response.edit_message(view=self)

        await interaction.followup.send("Added without rename", ephemeral=True)
        add_to_qbit(self.magnet)




# qBittorrent integration
def add_to_qbit(magnet: str, name: str | None = None):
    s = requests.Session()
    s.post(f"{QBIT_HOST}/api/v2/auth/login", data={"username": QBIT_USER, "password": QBIT_PASS})
    data = {
        "urls": magnet,
        "category": "radarr"
    }
    if name:
        data["rename"] = name
    s.post(f"{QBIT_HOST}/api/v2/torrents/add", data=data)

# Radarr integration
def add_to_radarr(title: str):
    payload = {
        "title": title,
        "qualityProfileId": 1,
        "rootFolderPath": RADARR_ROOT_FOLDER,
        "monitored": False,
        "addOptions": {
            "searchForMovie": False
        }
    }
    requests.post(
        f"{RADARR_HOST}/api/v3/movie",
        headers={"X-Api-Key": RADARR_API_KEY},
        json=payload,
        timeout=10
    )

bot.run(DISCORD_TOKEN)
