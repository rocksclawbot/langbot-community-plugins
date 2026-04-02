# Disaster Alert

Real-time earthquake, tsunami, and weather alerts pushed directly to your chat. Never miss a critical warning.

## Features

- **Multi-Source**: CEIC (China Earthquake Networks Center), USGS (Global), CMA Weather Warnings
- **Magnitude Filter**: Only alert earthquakes above your configured threshold
- **Manual Query**: Use `!quake list` command to check recent earthquakes on demand
- **Formatted Alerts**: Color-coded severity with location, depth, and time

## Configuration

| Setting | Description | Required |
|---------|-------------|----------|
| Check Interval | Polling interval in seconds (default: 120) | ❌ |
| Minimum Magnitude | Only alert earthquakes ≥ this magnitude (default: 3.0) | ❌ |
| Enable CEIC | Enable China Earthquake Networks Center (default: true) | ❌ |
| Enable USGS | Enable USGS global feed (default: false) | ❌ |
| Enable Weather | Enable CMA weather warnings (default: true) | ❌ |

## Commands

| Command | Description |
|---------|-------------|
| `!quake list` | Show recent earthquakes |

## Alert Format

```
🔴 【地震预警 - CEIC】
📍 四川省宜宾市
💥 震级: M5.2
📏 深度: 15 km
🕐 时间: 2026-04-03 02:15:30
```

- 🔴 M ≥ 5.0
- 🟡 M ≥ 4.0
- 🟢 M < 4.0
