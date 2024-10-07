import logging
import sys

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerType,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import cartesia, openai, deepgram, silero, elevenlabs
from livekit.plugins.elevenlabs import Voice, VoiceSettings



load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)



FELIX_VOICE = Voice(
    id="sRk0zCqhS2Cmv0bzx5wA",
    name="Felix",
    category="premade",
    settings=VoiceSettings(
        stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True
    ),
)



def prewarm(proc: JobProcess):
    logging.info("prewarming")
    proc.userdata["vad"] = silero.VAD.load()
    


async def entrypoint(ctx: JobContext):
    
    logging.info(f"function entrypoint")
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "Ты — голосовой помощник, созданный LiveKit. Твой интерфейс с пользователями будет голосовым."
            "Ты должны использовать короткие и лаконичные ответы и избегать использования непроизносимых знаков препинания."
            "Ты был создан в качестве демоверсии для демонстрации возможностей фреймворка агентов LiveKit."
        ),
    )

    logging.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logging.info(f"starting voice assistant for participant {participant.identity}")

    # This project is configured to use Deepgram STT, OpenAI LLM and TTS plugins
    # Other great providers exist like Cartesia and ElevenLabs
    # Learn more and pick the best one for your app:
    # https://docs.livekit.io/agents/plugins
    assistant = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=elevenlabs.TTS(voice=FELIX_VOICE),
        chat_ctx=initial_ctx,
    )

    assistant.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await assistant.say("Привет, чем я могу помочь тебе?", allow_interruptions=True)


if __name__ == "__main__":
    logging.info(f"Start voice assistant")
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            worker_type=WorkerType.ROOM
        ),
    )
