import logging

from langbot_plugin.api.definition.plugin import BasePlugin

logger = logging.getLogger(__name__)

EMOTION_KEYWORDS = {
    "happy": ["哈哈", "开心", "太好了", "棒", "nice", "great", "awesome", "😄", "😊", "🎉", "haha", "lol"],
    "sad": ["难过", "伤心", "遗憾", "可惜", "sorry", "unfortunately", "😢", "😭", "唉"],
    "angry": ["生气", "愤怒", "烦", "讨厌", "damn", "angry", "😡", "😤"],
    "excited": ["太棒了", "绝了", "牛", "amazing", "incredible", "wow", "🔥", "💪", "🚀", "!!"],
}


class TTSEmotionRouterPlugin(BasePlugin):

    async def initialize(self):
        logger.info("TTS Emotion Router initialized")

    def detect_emotion_by_keywords(self, text: str) -> str:
        text_lower = text.lower()
        scores = {emotion: 0 for emotion in EMOTION_KEYWORDS}
        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    scores[emotion] += 1
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return "neutral"

    async def detect_emotion_by_llm(self, text: str) -> str:
        model_uuid = self.get_config().get("llm_model")
        if not model_uuid:
            return self.detect_emotion_by_keywords(text)
        try:
            from langbot_plugin.api.entities.builtin.provider.message import (
                Message,
            )

            messages = [
                Message(
                    role="system",
                    content="Classify the emotion of the following text into exactly one of: happy, sad, angry, excited, neutral. Reply with ONLY the emotion word, nothing else.",
                ),
                Message(role="user", content=text[:500]),
            ]
            response = await self.invoke_llm(
                llm_model_uuid=model_uuid, messages=messages
            )
            content = response.content
            if isinstance(content, list):
                parts = [
                    e.text for e in content if hasattr(e, "text") and e.text
                ]
                content = " ".join(parts)
            if content:
                emotion = content.strip().lower()
                if emotion in ("happy", "sad", "angry", "excited", "neutral"):
                    return emotion
        except Exception as e:
            logger.warning(f"LLM emotion detection failed, falling back to keywords: {e}")
        return self.detect_emotion_by_keywords(text)

    def get_voice_for_emotion(self, emotion: str) -> str:
        config = self.get_config()
        voice_map = {
            "happy": config.get("happy_voice"),
            "sad": config.get("sad_voice"),
            "angry": config.get("angry_voice"),
            "excited": config.get("excited_voice"),
        }
        return voice_map.get(emotion) or config.get("default_voice", "alloy")

    def get_speed_for_emotion(self, emotion: str) -> float:
        if emotion == "excited":
            return self.get_config().get("speed_multiplier") or 1.15
        if emotion == "sad":
            return 0.9
        return 1.0

    async def synthesize(self, text: str, voice: str, speed: float) -> bytes:
        import aiohttp

        config = self.get_config()
        api_base = config.get("tts_api_base", "").rstrip("/")
        api_key = config.get("tts_api_key", "")
        model = config.get("tts_model", "tts-1")

        url = f"{api_base}/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": text[:4096],
            "voice": voice,
            "speed": speed,
            "response_format": "mp3",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(f"TTS API error {resp.status}: {body[:200]}")
                return await resp.read()
