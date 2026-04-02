import io
import logging
import tempfile

from langbot_plugin.api.definition.component import EventListener
from langbot_plugin.api.entities.builtin.pipeline import context, events
from langbot_plugin.api.entities.builtin.platform import message as platform_message

logger = logging.getLogger(__name__)


class TTSRouter(EventListener):
    """Intercept bot text responses, detect emotion, synthesize TTS with matching voice."""

    async def initialize(self):
        @self.handler(events.NormalMessageResponded)
        async def on_response(event_context: context.EventContext):
            event = event_context.event

            # Extract the response text
            response_text = ""
            if hasattr(event, "response_message_chain"):
                for component in event.response_message_chain:
                    if isinstance(component, platform_message.Plain):
                        response_text += component.text
            elif hasattr(event, "response_text"):
                response_text = event.response_text or ""

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

                # Write to temp file and send as voice
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    f.write(audio_data)
                    f.flush()
                    voice_msg = platform_message.MessageChain(
                        [platform_message.Record(file=f.name)]
                    )
                    await event_context.reply(voice_msg)

            except Exception as e:
                logger.error(f"TTS synthesis failed: {e}")
