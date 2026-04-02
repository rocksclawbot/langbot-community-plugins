import time
import logging
from collections import defaultdict

from langbot_plugin.api.definition.plugin import BasePlugin

logger = logging.getLogger(__name__)


class GroupAdminPlugin(BasePlugin):

    def __init__(self):
        super().__init__()
        # Flood detection: {group_id: {user_id: [timestamps]}}
        self._msg_times: dict = defaultdict(lambda: defaultdict(list))

    async def initialize(self):
        logger.info("Group Admin plugin initialized")

    def is_admin(self, user_id: str) -> bool:
        admin_str = self.get_config().get("admin_ids", "")
        if not admin_str:
            return True  # If not configured, allow all (rely on platform perms)
        admin_ids = [x.strip() for x in admin_str.split(",") if x.strip()]
        return user_id in admin_ids

    def check_flood(self, group_id: str, user_id: str) -> bool:
        """Returns True if user is flooding."""
        if not self.get_config().get("enable_auto_mute", False):
            return False

        now = time.time()
        threshold = self.get_config().get("flood_threshold") or 10
        window = 10  # seconds

        times = self._msg_times[group_id][user_id]
        times.append(now)
        # Keep only messages within the window
        self._msg_times[group_id][user_id] = [
            t for t in times if now - t < window
        ]

        return len(self._msg_times[group_id][user_id]) >= threshold

    def check_banned_words(self, text: str) -> str | None:
        """Returns the matched banned word, or None."""
        banned_str = self.get_config().get("banned_words", "")
        if not banned_str:
            return None
        words = [w.strip().lower() for w in banned_str.split(",") if w.strip()]
        text_lower = text.lower()
        for w in words:
            if w in text_lower:
                return w
        return None

    def parse_duration(self, s: str) -> int:
        """Parse duration string like '10m', '1h', '30s' into seconds."""
        s = s.strip().lower()
        if s.endswith("h"):
            return int(s[:-1]) * 3600
        elif s.endswith("m"):
            return int(s[:-1]) * 60
        elif s.endswith("s"):
            return int(s[:-1])
        else:
            return int(s)  # Assume seconds
