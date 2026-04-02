import logging

from langbot_plugin.api.definition.component import EventListener
from langbot_plugin.api.entities.builtin.pipeline import context, events
from langbot_plugin.api.entities.builtin.platform import message as platform_message

logger = logging.getLogger(__name__)


class FloodGuard(EventListener):
    """Detect message flooding and banned words in group messages."""

    async def initialize(self):

        @self.handler(events.GroupMessageReceived)
        async def on_group_msg(event_context: context.EventContext):
            event = event_context.event
            group_id = str(event.launcher_id)
            user_id = str(event.sender_id)

            # Extract text
            text_parts = []
            for component in event.message_chain:
                if isinstance(component, platform_message.Plain):
                    text_parts.append(component.text)
            text = "".join(text_parts).strip()

            # Check banned words
            matched = self.plugin.check_banned_words(text)
            if matched:
                logger.info(f"Banned word detected from {user_id} in {group_id}")
                try:
                    mute_duration = self.plugin.get_config().get("flood_mute_duration") or 300
                    await event_context.call_platform_api(
                        "set_group_ban",
                        group_id=group_id,
                        user_id=user_id,
                        duration=mute_duration,
                    )
                    await event_context.reply(
                        platform_message.MessageChain(
                            [platform_message.Plain(text=f"⚠️ 检测到违禁词，已禁言 {mute_duration // 60} 分钟。")]
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to mute for banned word: {e}")
                return

            # Check flood
            if self.plugin.check_flood(group_id, user_id):
                logger.info(f"Flood detected from {user_id} in {group_id}")
                try:
                    mute_duration = self.plugin.get_config().get("flood_mute_duration") or 300
                    await event_context.call_platform_api(
                        "set_group_ban",
                        group_id=group_id,
                        user_id=user_id,
                        duration=mute_duration,
                    )
                    await event_context.reply(
                        platform_message.MessageChain(
                            [platform_message.Plain(text=f"🔇 检测到刷屏行为，已禁言 {mute_duration // 60} 分钟。")]
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to auto-mute flood: {e}")
