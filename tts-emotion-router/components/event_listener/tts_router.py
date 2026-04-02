import base64
import logging

from langbot_plugin.api.definition.components.common.event_listener import EventListener
from langbot_plugin.api.entities.context import EventContext
from langbot_plugin.api.entities import events
from langbot_plugin.api.entities.builtin.platform import message as platform_message

logger = logging.getLogger(__name__)


class TTSRouter(EventListener):
    """Intercept bot text responses, detect emotion, synthesize TTS with matching voice."""

    async def initialize(self):

        @self.handler(events.NormalMessageResponded)
        async def on_response(ctx: EventContext):
            # Extract response text
            response_text = ""
            if hasattr(ctx.event, "response_message_chain"):
                for component in ctx.event.response_message_chain:
                    if isinstance(component, platform_message.Plain):
                        response_text += component.text

            response_text = response_text.strip()
            if not response_text or len(response_text) < 2:
                return

            config = self.plugin.get_config()
            if not config.get("tts_api_base") or not config.get("tts_api_key"):
                return

            try:
                emotion = await self.plugin.detect_emotion_by_llm(response_text)
                voice = self.plugin.get_voice_for_emotion(emotion)
                speed = self.plugin.get_speed_for_emotion(emotion)

                logger.debug(f"Emotion: {emotion}, Voice: {voice}, Speed: {speed}")

                audio_data = await self.plugin.synthesize(response_text, voice, speed)

                audio_b64 = base64.b64encode(audio_data).decode("utf-8")
                await ctx.reply(
                    platform_message.MessageChain([platform_message.Voice(base64=audio_b64)])
                )

            except Exception as e:
                logger.error(f"TTS synthesis failed: {e}")
