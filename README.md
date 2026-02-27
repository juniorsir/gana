# 🌌 GANA PLAYER

> **The Ultimate Cyberpunk CLI Music Player for Hackers.**

[![PyPI version](https://badge.fury.io/py/gana-player.svg)](https://badge.fury.io/py/gana-player)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**GANA** is a high-performance, terminal-based YouTube music player designed for Linux and Termux.  
It features a 3D Hyperdrive UI, AI-powered recommendations, background playback with lock-screen controls, and automatic offline caching.

---
```bash
curl -fsSL https://juniorsir.github.io/gana/public.key | gpg --dearmor | tee $PREFIX/etc/apt/trusted.gpg.d/gana.gpg > /dev/null<br><br>
# 2. Add the Repository
echo "deb https://juniorsir.github.io/gana/ ./" > $PREFIX/etc/apt/sources.list.d/gana.list<br><br>
# 3. Install
pkg update && pkg install gana
````
# 🚀 Quick Start

## 1️⃣ Install via Pip (Universal)

Works on any system with Python 3.8+.

```bash
pip install gana-player
```

Run it:

```bash
gana
# OR
gana-player
```

---

## 2️⃣ Install on Termux (Android)

For the full experience (hardware controls, notifications), install the API dependencies first.

```bash
pkg update
pkg install python mpv ffmpeg termux-api
pip install gana-player
gana
```

> ⚠️ You must install the **Termux:API** app (Play Store or F-Droid) for lock screen controls to work.

---

# 🎮 Controls & Hotkeys

## 🖥 Global CLI Commands

You don't need to open the UI to use GANA.

```bash
gana search "lofi hip hop"   # Jump straight to search results
gana play "starboy"          # Instantly auto-play best match
gana resume                  # Continue where you left off
gana history                 # View and manage playback history
gana help                    # Show the interactive manual
```

---

## 🎵 In-Player Hotkeys

| Key        | Action |
|------------|--------|
| `SPACE`    | Pause / Resume |
| `N / P`    | Next / Previous Song |
| `← / →`    | Seek -10s / +10s |
| `S`        | Open ✨ AI Recommendations HUD |
| `V`        | Open Queue Manager |
| `R`        | Toggle Loop (Sequence ➡ / One 🔂 / All 🔁) |
| `B`        | Background Mode (Keep playing while browsing menu) |
| `Q`        | Stop & Return to Menu |

---

## 📂 Queue Manager (Press `V`)

| Key     | Action |
|---------|--------|
| `ENTER` | Jump to selected song |
| `D`     | Delete song from queue |
| `R`     | Toggle Loop Mode |

---

# ✨ Features Breakdown

## 🌌 3D Hyperdrive UI

The interface reacts to your music.

- When playing → starfield accelerates into hyperdrive  
- When paused → starfield drifts slowly  
- A sine-wave rainbow visualizer dances above the seek bar  

---

## 🧠 AI Recommendations

Press `S` while playing any song.

GANA analyzes:
- Current track  
- Recent search history  

It generates **4 intelligent recommendations**.  
Select one to instantly queue it next.

---

## 📡 Offline Caching (Smart Data Mode)

- Every song is cached automatically to:
  ```
  ~/.gana/cache/
  ```
- Replaying a cached song uses **0 data**
- Auto-cleans cache (keeps last 5 songs)
- Works completely offline

### 🔌 Offline Mode

Turn off WiFi → Open History → Play cached songs instantly.

---

## 📱 Android Integration

- 🔒 **Lock Screen Support**
  - Song title
  - Album art
  - Offline Support 

- 🔔 **Notification Controls**
  - Tap notification to Pause/Play
  - Use Next / Prev buttons
  - Use Single tap to add sleep time

---

# 🛠 Troubleshooting

## ❌ "mpv not found"

GANA requires `mpv` to play audio.

**Linux:**
```bash
sudo apt install mpv
```

**Termux:**
```bash
pkg install mpv
```

---

## ❌ Notifications not showing on Android

- Ensure:
  ```bash
  pkg install termux-api
  ```
- Install **Termux:API** app
- Restart Termux

---

## ❌ Visualizer looks broken / text glitchy

Ensure your terminal supports 256 colors:

```bash
export TERM=xterm-256color
```

---

# 📦 Installation for Advanced Users

## Install via DEB (Debian / Ubuntu)

If a `.deb` release is provided:

```bash
sudo apt install ./gana_1.0.0_all.deb
```

---

## 🔨 Build from Source

```bash
git clone https://github.com/yourusername/gana
cd gana
pip install .
```

---

# ❤️ Made for the CLI Community

Built with love for hackers, developers, and terminal enthusiasts.

---

## 📄 License

MIT License © 2026

# gana_source
