# Magnetarr Discord Bot

Magnetarr is a lightweight **Discord slash-command bot** that sends **magnet links** to **qBittorrent** and optionally registers the media in **Radarr** or **Sonarr** using an IMDb ID.

It is designed to fit cleanly into common **Arr stacks** and works perfectly in **Docker / Unraid / self-hosted environments**.

*WORK IN PROGRESS*

---

## ✨ Features

✔ Uses **Slash Commands** (`/magnet_movie`, `/magnet_series`)  
✔ Adds magnet links to **qBittorrent** with category  
✔ Integrates with **Radarr** and **Sonarr**  
✔ Sets media entries to “Unmonitored”  
✔ Optional: rename torrent before adding  
✔ Optional: attach IMDB ID for Radarr/Sonarr detection  
✔ Docker-ready, easy Unraid deployment

---

## 📌 Commands

### `/magnet_movie`

Add a **movie** magnet and optionally notify Radarr.

**Arguments**

| Name      | Required | Description            |
| --------- | -------- | ---------------------- |
| `magnet`  | ✅        | Magnet link            |
| `name`    | ❌        | Rename torrent         |
| `tmdb_id` | ❌        | TMDb ID sent to Radarr |

**Example**

```
/magnet_movie magnet:magnet:?xt=urn:btih:... name:"Dune (2024)" imdb_id:tt15239678
```

---

### `/magnet_series`

Add a **TV series** magnet and optionally notify Sonarr.

**Arguments**

| Name      | Required | Description            |
| --------- | -------- | ---------------------- |
| `magnet`  | ✅        | Magnet link            |
| `name`    | ❌        | Rename torrent         |
| `imdb_id` | ❌        | IMDb ID sent to Sonarr |

**Example**

```
/magnet_tv magnet:magnet:?xt=urn:btih:... name:"The Last of Us" imdb_id:tt3581920
```

---

### `/magnet_help`

Display help information for all commands.

---

## 🛠️ Requirements

* Python **3.10+**
* Discord Bot Token
* qBittorrent (Web API enabled)
* Radarr (optional)
* Sonarr (optional)

---

## 📦 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/gryalphk/magnetarr.git
cd magnetarr
```

---

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

**Required packages**

* `discord.py`
* `requests`

---

### 3️⃣ Environment Variables

Create a `.env` file or set the variables in your container:

```env
DISCORD_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_discord_server_id

QB_URL=http://qbittorrent:8080
QB_USER=admin
QB_PASS=adminadmin
RADARR_ROOT =/media

RADARR_URL=http://radarr:7878
RADARR_API_KEY=radarr_api_key

SONARR_URL=http://sonarr:8989
SONARR_API_KEY=sonarr_api_key
```

> **Note**
> Radarr and Sonarr are optional — if no IMDb ID is provided, the bot will only add the magnet to qBittorrent.

---

## 🚀 Running the Bot

```bash
python bot/main.py
```

On first startup, slash commands will be registered instantly for the configured guild.

---

## 🐳 Docker (Optional)

This bot works perfectly in Docker / Unraid environments.

Basic example:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "bot/main.py"]
```

---

## 🔐 Permissions

The bot requires:

* `applications.commands`
* `Send Messages`

No privileged intents are required.

---

## 🧠 How It Works

1. User runs a slash command in Discord
2. Bot sends magnet link to **qBittorrent**
3. Torrent is optionally renamed
4. Torrent category is set:
   * `radarr` for movies
   * `sonarr` for TV
5. TMDb ID & Name (if provided) is sent to Radarr or Sonarr
