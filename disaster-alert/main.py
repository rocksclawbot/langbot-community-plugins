import asyncio
import time
import logging
from typing import Optional

import aiohttp

from langbot_plugin.api.definition.plugin import BasePlugin

logger = logging.getLogger(__name__)


class DisasterAlertPlugin(BasePlugin):

    def __init__(self):
        super().__init__()
        self._seen_ids: set = set()
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self):
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Disaster Alert plugin initialized")

    async def destroy(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _poll_loop(self):
        # Wait a bit for system to stabilize
        await asyncio.sleep(10)
        while self._running:
            try:
                interval = self.get_config().get("check_interval") or 120
                alerts = []

                if self.get_config().get("enable_ceic", True):
                    alerts.extend(await self._fetch_ceic())

                if self.get_config().get("enable_usgs", False):
                    alerts.extend(await self._fetch_usgs())

                if self.get_config().get("enable_weather", True):
                    alerts.extend(await self._fetch_weather())

                for alert in alerts:
                    if alert["id"] not in self._seen_ids:
                        self._seen_ids.add(alert["id"])
                        await self._broadcast(alert)

                # Cap seen IDs to prevent memory leak
                if len(self._seen_ids) > 5000:
                    self._seen_ids = set(list(self._seen_ids)[-2000:])

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Poll loop error: {e}")
                await asyncio.sleep(60)

    async def _fetch_ceic(self) -> list:
        """Fetch recent earthquakes from CEIC (China Earthquake Networks Center)."""
        url = "https://news.ceic.ac.cn/ajax/google"
        min_mag = self.get_config().get("min_magnitude") or 3.0
        alerts = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json(content_type=None)
                    for eq in data:
                        mag = float(eq.get("M", 0))
                        if mag >= min_mag:
                            eq_id = eq.get("id") or eq.get("CATA_ID", str(eq.get("O_TIME", "")))
                            alerts.append({
                                "id": f"ceic_{eq_id}",
                                "type": "earthquake",
                                "source": "CEIC",
                                "magnitude": mag,
                                "location": eq.get("LOCATION_C", eq.get("LOCATION", "Unknown")),
                                "depth": eq.get("EPI_DEPTH", "N/A"),
                                "time": eq.get("O_TIME", ""),
                                "lat": eq.get("EPI_LAT", ""),
                                "lon": eq.get("EPI_LON", ""),
                            })
        except Exception as e:
            logger.warning(f"CEIC fetch failed: {e}")
        return alerts

    async def _fetch_usgs(self) -> list:
        """Fetch recent earthquakes from USGS GeoJSON feed."""
        min_mag = self.get_config().get("min_magnitude") or 3.0
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_hour.geojson"
        alerts = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    for feature in data.get("features", []):
                        props = feature.get("properties", {})
                        mag = props.get("mag", 0) or 0
                        if mag >= min_mag:
                            coords = feature.get("geometry", {}).get("coordinates", [0, 0, 0])
                            alerts.append({
                                "id": f"usgs_{feature.get('id', '')}",
                                "type": "earthquake",
                                "source": "USGS",
                                "magnitude": mag,
                                "location": props.get("place", "Unknown"),
                                "depth": f"{coords[2]:.1f} km" if len(coords) > 2 else "N/A",
                                "time": props.get("time", ""),
                                "lat": coords[1] if len(coords) > 1 else "",
                                "lon": coords[0] if len(coords) > 0 else "",
                            })
        except Exception as e:
            logger.warning(f"USGS fetch failed: {e}")
        return alerts

    async def _fetch_weather(self) -> list:
        """Fetch weather warnings from CMA (China Meteorological Administration)."""
        url = "https://devapi.qweather.com/v7/warning/now"
        # Using free public endpoint that doesn't require key
        alt_url = "https://whicdn.com/weather-warning/china.json"
        alerts = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(alt_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json(content_type=None)
                    warnings = data if isinstance(data, list) else data.get("data", [])
                    for w in warnings[:20]:  # Limit to 20 most recent
                        w_id = w.get("id") or w.get("alertId", str(hash(str(w)[:100])))
                        alerts.append({
                            "id": f"cma_{w_id}",
                            "type": "weather",
                            "source": "CMA",
                            "title": w.get("title", "Weather Warning"),
                            "level": w.get("level", w.get("severityColor", "")),
                            "description": (w.get("text") or w.get("description", ""))[:300],
                            "time": w.get("pubTime") or w.get("sendTime", ""),
                        })
        except Exception as e:
            logger.warning(f"Weather fetch failed: {e}")
        return alerts

    def format_alert(self, alert: dict) -> str:
        if alert["type"] == "earthquake":
            emoji = "🔴" if alert["magnitude"] >= 5.0 else "🟡" if alert["magnitude"] >= 4.0 else "🟢"
            return (
                f"{emoji} 【地震预警 - {alert['source']}】\n"
                f"📍 {alert['location']}\n"
                f"💥 震级: M{alert['magnitude']}\n"
                f"📏 深度: {alert['depth']}\n"
                f"🕐 时间: {alert['time']}\n"
            )
        elif alert["type"] == "weather":
            return (
                f"⚠️ 【气象预警】\n"
                f"📋 {alert.get('title', 'Warning')}\n"
                f"🔶 级别: {alert.get('level', 'N/A')}\n"
                f"📝 {alert.get('description', '')}\n"
                f"🕐 发布: {alert.get('time', '')}\n"
            )
        return str(alert)

    async def _broadcast(self, alert: dict):
        """Send alert message. Uses send_message API if available."""
        text = self.format_alert(alert)
        logger.info(f"Broadcasting alert: {alert['id']}")
        try:
            from langbot_plugin.api.entities.builtin.platform import (
                message as platform_message,
            )

            msg = platform_message.MessageChain([platform_message.Plain(text=text)])
            await self.send_message(message=msg)
        except Exception as e:
            logger.error(f"Failed to broadcast alert: {e}")

    async def get_recent_quakes(self) -> str:
        """Get a summary of recent earthquakes for command use."""
        alerts = []
        if self.get_config().get("enable_ceic", True):
            alerts.extend(await self._fetch_ceic())
        if self.get_config().get("enable_usgs", False):
            alerts.extend(await self._fetch_usgs())

        if not alerts:
            return "📊 最近没有符合条件的地震记录。"

        alerts.sort(key=lambda x: x.get("magnitude", 0), reverse=True)
        lines = ["📊 最近地震列表：\n"]
        for a in alerts[:10]:
            lines.append(f"• M{a['magnitude']} | {a['location']} | {a['time']}")
        return "\n".join(lines)
