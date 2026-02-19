import os
import re
import discord
from discord import app_commands
import aiohttp

INTENTS = discord.Intents.default()
CLIENT = discord.Client(intents=INTENTS)
TREE = app_commands.CommandTree(CLIENT)

DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

QB_URL = os.getenv("QB_URL")
QB_USER = os.getenv("QB_USER")
QB_PASS = os.getenv("QB_PASS")

RADARR_URL = os.getenv("RADARR_URL")
RADARR_KEY = os.getenv("RADARR_KEY")
RADARR_ROOT = os.getenv("RADARR_ROOT")

SONARR_URL = os.getenv("SONARR_URL")
SONARR_KEY = os.getenv("SONARR_KEY")

TMDB_API_KEY = "YOUR_TMDB_KEY"

# ======================================================
# ================= TMDB HELPERS =======================
# ======================================================

async def tmdb_search(query: str):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return []

            data = await resp.json()
            return data.get("results", [])[:10]


# ======================================================
# ================= UI COMPONENTS ======================
# ======================================================

class MovieSelect(discord.ui.Select):
    def __init__(self, movies, magnet, rename):
        self.movies = movies
        self.magnet = magnet
        self.rename = rename

        options = [
            discord.SelectOption(
                label=f"{m['title']} ({m.get('release_date','')[:4]})",
                value=str(m["id"])
            )
            for m in movies
        ]

        super().__init__(
            placeholder="Select movie from TMDB...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        movie_id = self.values[0]
        movie = next(m for m in self.movies if str(m["id"]) == movie_id)

        release_date = movie.get("release_date", "")
        year = release_date[:4] if release_date else "Unknown"

        # 🔹 CLEAN TITLE (keep - & . () [])
        raw_title = movie["title"]
        cleaned_title = re.sub(r"[^A-Za-z0-9\-\&\.\(\)\[\] ]+", "", raw_title)
        cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip()

        full_title = f"{cleaned_title} ({year})"

        poster = (
            f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}"
            if movie.get("poster_path")
            else None
        )

        embed = discord.Embed(
            title=full_title,
            description=movie.get("overview", "No overview available."),
            color=0x00ff99
        )

        if poster:
            embed.set_image(url=poster)

        view = ConfirmView(movie_id, self.magnet, self.rename, full_title)

        await interaction.response.edit_message(embed=embed, view=view)


class ConfirmView(discord.ui.View):
    def __init__(self, tmdb_id, magnet, rename, title):
        super().__init__(timeout=120)
        self.tmdb_id = tmdb_id
        self.magnet = magnet
        self.rename = rename
        self.title = title

    async def disable_all(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        async with aiohttp.ClientSession() as session:
            await radarr_add_unmonitored(session, self.tmdb_id, self.title)
            await qb_add_torrent(session, self.magnet, "radarr", self.title)

        await self.disable_all()

        await interaction.response.edit_message(
            content=f"🎬 Movie **{self.title}** added successfully!",
            embed=None,
            view=None
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.stop()
        self.clear_items()

        await interaction.response.edit_message(
            content="❌ Operation cancelled.",
            embed=None,
            view=None
        )


# ======================================================
# ================= QBITTORRENT ========================
# ======================================================

async def qb_login(session):
    r = await session.post(
        f"{QB_URL}/api/v2/auth/login",
        data={"username": QB_USER, "password": QB_PASS}
    )

    if r.status != 200:
        text = await r.text()
        raise Exception(f"qBittorrent login failed: {r.status} — {text}")


async def qb_add_torrent(session, magnet, category, rename=None):
    data = {
        "urls": magnet,
        "category": category
    }

    if rename:
        data["rename"] = rename

    await qb_login(session)

    async with session.post(f"{QB_URL}/api/v2/torrents/add", data=data) as resp:
        return resp.status == 200


# ======================================================
# ================= RADARR =============================
# ======================================================

async def radarr_add_unmonitored(session, tmdb_id, name):

    headers = {"X-Api-Key": RADARR_KEY}

    payload = {
        "title": name,
        "qualityProfileId": 1,
        "rootFolderPath": RADARR_ROOT,
        "addOptions": {"searchForMovie": False},
        "monitored": False,
        "tmdbId": tmdb_id
    }

    async with session.post(
        f"{RADARR_URL}/api/v3/movie",
        json=payload,
        headers=headers
    ) as resp:
        return resp.status in (200, 201)


# ======================================================
# ================= SONARR =============================
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
# ================= COMMANDS ===========================
# ======================================================

@TREE.command(
    name="magnet_movie",
    description="Search TMDB and add magnet to Radarr + qBittorrent"
)
@app_commands.describe(
    magnet="Magnet link",
    movie="Movie name to search on TMDB",
)
async def magnet_movie(
    interaction: discord.Interaction,
    magnet: str,
    movie: str
):

    if int(interaction.guild_id) != int(DISCORD_GUILD_ID):
        return await interaction.response.send_message(
            "Not allowed here.",
            ephemeral=True
        )

    await interaction.response.defer()

    results = await tmdb_search(movie)

    if not results:
        return await interaction.followup.send("No results found on TMDB.")

    class SearchView(discord.ui.View):
        def __init__(self, results, magnet, rename):
            super().__init__(timeout=120)
            self.add_item(MovieSelect(results, magnet, rename))

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True

    view = SearchView(results, magnet, movie)

    await interaction.followup.send(
        content="Select the correct movie:",
        view=view
    )


@TREE.command(
    name="magnet_series",
    description="Add magnet to Sonarr + qBittorrent"
)
@app_commands.describe(
    magnet="Magnet link",
    name="Optional rename",
    imdb_id="Optional IMDB ID"
)
async def magnet_series(
    interaction: discord.Interaction,
    magnet: str,
    name: str | None = None,
    imdb_id: str | None = None
):

    if interaction.guild_id != DISCORD_GUILD_ID:
        return await interaction.response.send_message(
            "Not allowed here.",
            ephemeral=True
        )

    async with aiohttp.ClientSession() as session:
        await sonarr_add_unmonitored(session, imdb_id)
        await qb_add_torrent(session, magnet, "sonarr", name)

    await interaction.response.send_message("📺 Series magnet processed!")


# ======================================================
# ================= STARTUP ============================
# ======================================================

@CLIENT.event
async def on_ready():
    guild = discord.Object(id=DISCORD_GUILD_ID)
    synced = await TREE.sync(guild=guild)
    print(f"Bot logged in as {CLIENT.user}")
    print(f"Synced {len(synced)} commands.")

CLIENT.run(DISCORD_TOKEN)
