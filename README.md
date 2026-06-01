# Micoraceel

This program is designed for Windows users inside the Great Firewall of China to bypass censorship and access the borderless internet for watching and browsing. It is an EXE file — just download and run it directly.

## Features

- Automatically fetches subscription nodes (VLESS)
- TCP concurrent speed test, auto-selects the fastest 5 nodes
- xray-core load balancing with traffic distribution
- Direct connection for China mainland traffic (geosite:cn + geoip:cn)
- Speed test refresh every 10 minutes, subscription update every 3 hours
- Automatically sets/clears system proxy
- Runs silently in the background with tray icon
- Standalone EXE, no dependencies required

## Download

Download the latest release from the [Releases page](https://github.com/rebecaachambers/Micoraceel/releases).

## Usage

1. Download `Micoraceel.exe`
2. Double-click to run (no installation required)
3. The program will automatically:
   - Fetch and parse subscription nodes
   - Test node speeds and select the fastest 5
   - Start xray-core with load balancing
   - Enable system proxy
4. Right-click the tray icon to exit (clears all proxy settings)

## Build from Source

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --add-data "xray-core;xray-core" --name "Micoraceel" app.py
```
