from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
import speech_recognition as sr
import pyttsx3
import os
from pathlib import Path
from pydub import AudioSegment
import uuid
import logging

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

# Ensure data directories exist
TEMP_AUDIO_DIR = Path("data/temp_audio")
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class TTSRequest(BaseModel):
    text: str

@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """
    Convert uploaded audio file to text.
    Accepts various audio formats (wav, mp3, ogg, webm, etc).
    """
    try:
        # Generate unique filename for temp storage
        file_id = str(uuid.uuid4())
        original_ext = file.filename.split('.')[-1] if '.' in file.filename else "wav"
        temp_input_path = TEMP_AUDIO_DIR / f"{file_id}.{original_ext}"
        wav_output_path = TEMP_AUDIO_DIR / f"{file_id}.wav"

        # Save uploaded file
        with open(temp_input_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Convert to WAV (speech_recognition needs WAV)
        try:
            audio = AudioSegment.from_file(str(temp_input_path))
            audio.export(str(wav_output_path), format="wav")
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise HTTPException(status_code=400, detail=f"Could not convert audio file: {str(e)}")

        # Perform STT
        r = sr.Recognizer()
        with sr.AudioFile(str(wav_output_path)) as source:
            audio_data = r.record(source)
            try:
                text = r.recognize_google(audio_data)
                return {"text": text}
            except sr.UnknownValueError:
                return {"text": ""} # Could not understand audio
            except sr.RequestError as e:
                logger.error(f"STT Service Error: {e}")
                raise HTTPException(status_code=503, detail="Speech service unavailable")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp files
        if 'temp_input_path' in locals() and temp_input_path.exists():
            try:
                os.remove(temp_input_path)
            except: 
                pass
        if 'wav_output_path' in locals() and wav_output_path.exists():
            try:
                os.remove(wav_output_path)
            except:
                pass


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to audio (WAV).
    Returns a FileResponse with the audio.
    """
    try:
        file_id = str(uuid.uuid4())
        output_file_path = TEMP_AUDIO_DIR / f"{file_id}.wav"

        # Initialize engine
        # Note: pyttsx3 init can be problematic in multithreaded envs like FastAPI.
        # Ideally we'd have a worker or singleton, but for simple use case:
        engine = pyttsx3.init()
        
        # Configure voice (optional, user asked to use backend/tts.py logical style)
        voices = engine.getProperty('voices')
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id) # Female voice typically
        engine.setProperty('rate', 150)

        # Save to file
        engine.save_to_file(request.text, str(output_file_path))
        engine.runAndWait()
        
        # Check if file created
        if not output_file_path.exists():
            raise HTTPException(status_code=500, detail="Failed to generate audio file")

        # Return file
        return FileResponse(
            path=output_file_path,
            media_type="audio/wav",
            filename="response.wav"
        )

    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
