import discord
from discord.ext import commands
from discord import app_commands
import requests
import re

import os

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
QBIT_HOST = os.environ["QBIT_HOST"]
QBIT_USER = os.environ["QBIT_USER"]
QBIT_PASS = os.environ["QBIT_PASS"]

RADARR_HOST = os.environ["RADARR_HOST"]
RADARR_API_KEY = os.environ["RADARR_API_KEY"]
RADARR_ROOT_FOLDER = os.environ["RADARR_ROOT_FOLDER"]


MAGNET_RE = re.compile(r"magnet:\?xt=urn:btih:[a-zA-Z0-9]+")


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
	await bot.tree.sync()
	print(f"Logged in as {bot.user}")


@bot.tree.command(name="magnet", description="Add a magnet link")
@app_commands.describe(link="Magnet link")
async def magnet(interaction: discord.Interaction, link: str):
	if not MAGNET_RE.match(link):
		await interaction.response.send_message("Invalid magnet link", ephemeral=True)
		return


	view = RenameView(link)
	await interaction.response.send_message("Rename torrent?", view=view, ephemeral=True)


class RenameView(discord.ui.View):
	def __init__(self, magnet):
		super().__init__(timeout=60)
		self.magnet = magnet


	@discord.ui.button(label="Rename", style=discord.ButtonStyle.primary)
	async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_message("Send new name:", ephemeral=True)


		def check(m):
			return m.author == interaction.user


		msg = await bot.wait_for("message", check=check)
		add_to_qbit(self.magnet, msg.content)
		add_to_radarr(msg.content)
		await interaction.followup.send("Added with renamed title", ephemeral=True)


	@discord.ui.button(label="Keep Name", style=discord.ButtonStyle.secondary)
	async def keep(self, interaction: discord.Interaction, button: discord.ui.Button):
		add_to_qbit(self.magnet, None)
		await interaction.followup.send("Added without rename", ephemeral=True)


# qBittorrent
def add_to_qbit(magnet, name=None):
	s = requests.Session()
	s.post(f"{QBIT_HOST}/api/v2/auth/login", data={"username": QBIT_USER, "password": QBIT_PASS})
	data = {"urls": magnet, "category": "radarr"}
	if name:
		data["rename"] = name
	s.post(f"{QBIT_HOST}/api/v2/torrents/add", data=data)


# Radarr
def add_to_radarr(title):
	payload = {
		"title": title,
		"qualityProfileId": 1,
		"rootFolderPath": RADARR_ROOT_FOLDER,
		"monitored": False,
		"addOptions": {"searchForMovie": False}
	}
	requests.post(
		f"{RADARR_HOST}/api/v3/movie",
		headers={"X-Api-Key": RADARR_API_KEY},
		json=payload
	)



bot.run(DISCORD_TOKEN)
