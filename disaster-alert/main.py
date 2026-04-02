import asyncio
import logging
from typing import Optional

import aiohttp

from langbot_plugin.api.definition.plugin import BasePlugin

logger = logging.getLogger(__name__)


class DisasterAlertPlugin(BasePlugin):

    def __init__(self):
        super().__init__()
        self._recent_alerts: list = []

    async def initialize(self):
        logger.info("Disaster Alert plugin initialized")

    async def fetch_ceic(self) -> list:
        """Fetch recent earthquakes from CEIC."""
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
                            alerts.append({
                                "source": "CEIC",
                                "magnitude": mag,
                                "location": eq.get("LOCATION_C", eq.get("LOCATION", "Unknown")),
                                "depth": eq.get("EPI_DEPTH", "N/A"),
                                "time": eq.get("O_TIME", ""),
                            })
        except Exception as e:
            logger.warning(f"CEIC fetch failed: {e}")
        return alerts

    async def fetch_usgs(self) -> list:
        """Fetch recent earthquakes from USGS."""
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
                                "source": "USGS",
                                "magnitude": mag,
                                "location": props.get("place", "Unknown"),
                                "depth": f"{coords[2]:.1f} km" if len(coords) > 2 else "N/A",
                                "time": props.get("time", ""),
                            })
        except Exception as e:
            logger.warning(f"USGS fetch failed: {e}")
        return alerts

    async def get_recent_quakes(self) -> str:
        """Get a formatted summary of recent earthquakes."""
        alerts = []
        if self.get_config().get("enable_ceic", True):
            alerts.extend(await self.fetch_ceic())
        if self.get_config().get("enable_usgs", False):
            alerts.extend(await self.fetch_usgs())

        if not alerts:
            return "📊 最近没有符合条件的地震记录。"

        alerts.sort(key=lambda x: x.get("magnitude", 0), reverse=True)
        lines = ["📊 最近地震列表：\n"]
        for a in alerts[:15]:
            emoji = "🔴" if a["magnitude"] >= 5.0 else "🟡" if a["magnitude"] >= 4.0 else "🟢"
            lines.append(f"{emoji} M{a['magnitude']} | {a['location']} | 深度 {a['depth']} | {a['time']}")
        return "\n".join(lines)
