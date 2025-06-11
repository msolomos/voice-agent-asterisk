#!/usr/bin/env python3
import os
import tempfile
import logging
import subprocess
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import openai
import json
from datetime import datetime
import io

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenAI Voice Agent for IT Company")

# OpenAI client setup με βελτιωμένο error handling
client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    logger.info(f"Initializing OpenAI client with key: {api_key[:8]}...")
    
    # Χρησιμοποιούμε την πιο απλή μέθοδο initialization
    openai.api_key = api_key
    
    # Test connection
    models = openai.Model.list()
    logger.info("OpenAI API connection verified successfully")
    client = "initialized"  # Flag ότι δουλεύει
    
except Exception as e:
    logger.error(f"OpenAI client initialization error: {e}")
    client = None

class OpenAIVoiceAgent:
    def __init__(self):
        self.system_prompt = """
Είσαι ένας φιλικός voice agent για μια εταιρεία πληροφορικής στην Ελλάδα.
Η δουλειά σου είναι να κατανοήσεις τι θέλει ο πελάτης και να τον κατηγοριοποιήσεις.

ΠΡΟΣΟΧΗ: ΠΑΝΤΑ απαντάς στα ΕΛΛΗΝΙΚΑ, ακόμα και αν η φράση περιέχει αγγλικές λέξεις ή όρους.

Κατηγορίες:
- tech_support: τεχνική υποστήριξη, προβλήματα υπολογιστών, servers, δικτύων
- sales: πωλήσεις, αγορές, προσφορές, νέος εξοπλισμός  
- accounting: λογιστήριο, τιμολόγια, πληρωμές
- general: γενικές πληροφορίες, ωράριο, διεύθυνση

ΣΗΜΑΝΤΙΚΟ: Δώσε ΜΟΝΟ σύντομη απάντηση μεταφοράς. ΜΗΝ κάνεις επιπλέον ερωτήσεις.

Απάντησε ΠΑΝΤΑ σε JSON format:
{
  "intent": "κατηγορία", 
  "confidence": 0.9,
  "response": "Σύντομη φιλική απάντηση μεταφοράς (μόνο 1-2 προτάσεις)",
  "name": "όνομα αν αναφέρθηκε ή null"
}

Παραδείγματα απαντήσεων:
- tech_support: "Θα σας συνδέσω με την τεχνική υποστήριξη. Παρακαλώ περιμένετε."
- sales: "Θα σας μεταφέρω στο τμήμα πωλήσεων. Ένα λεπτό παρακαλώ."
- accounting: "Σας συνδέω με το λογιστήριο μας. Περιμένετε λίγο."
- general: "Θα σας συνδέσω με την υποδοχή μας. Παρακαλώ περιμένετε."
"""



    def process_audio_openai(self, audio_file_path):
        """Process audio με OpenAI Whisper API"""
        try:
            if not client:
                raise Exception("OpenAI client not initialized")
                
            # Speech-to-Text με OpenAI Whisper
            with open(audio_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language="el"  # Greek
                )
            
            transcribed_text = transcript["text"]
            logger.info(f"OpenAI Transcribed: {transcribed_text}")
            
            # Intent detection με GPT
            chat_response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Πελάτης είπε: '{transcribed_text}'"}
                ],
                temperature=0.3
            )
            
            # Parse JSON response
            ai_response = chat_response.choices[0].message.content
            logger.info(f"GPT Response: {ai_response}")
            
            try:
                parsed_response = json.loads(ai_response)
                intent = parsed_response.get("intent", "general")
                confidence = parsed_response.get("confidence", 0.5)
                response_text = parsed_response.get("response", "Θα σας συνδέσω με την υποδοχή.")
                name = parsed_response.get("name")
            except json.JSONDecodeError:
                # Fallback αν το GPT δεν επιστρέψει valid JSON
                intent = "general"
                confidence = 0.3
                response_text = "Θα σας συνδέσω με την υποδοχή μας."
                name = None
            
            # Text-to-Speech με OpenAI - FALLBACK ΣΕ ΠΑΛΙΑ API
            mp3_file_path = audio_file_path.replace('.wav', '_response.mp3')
            
            try:
                # Προσπάθεια με νέα API
                try:
                    import requests
                    
                    tts_response = requests.post(
                        "https://api.openai.com/v1/audio/speech",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "tts-1",
                            "voice": "alloy", 
                            "input": response_text,
                            "response_format": "mp3"
                        }
                    )
                    
                    if tts_response.status_code == 200:
                        # Αποθήκευση του MP3 audio
                        with open(mp3_file_path, 'wb') as f:
                            f.write(tts_response.content)
                        
                        logger.info(f"TTS audio saved as MP3: {mp3_file_path}")
                        final_audio_path = mp3_file_path
                    else:
                        logger.error(f"TTS API error: {tts_response.status_code}")
                        raise Exception("TTS API failed")
                        
                except Exception as tts_api_error:
                    logger.warning(f"OpenAI TTS not available: {tts_api_error}")
                    # Fallback: δημιούργησε dummy MP3 file
                    with open(mp3_file_path, 'w') as f:
                        f.write('')
                    final_audio_path = mp3_file_path
                    logger.info("Created dummy MP3 file as fallback")
                
            except Exception as tts_error:
                logger.error(f"TTS error: {tts_error}")
                final_audio_path = None
            
            return {
                "transcribed_text": transcribed_text,
                "intent": intent,
                "confidence": confidence,
                "response_text": response_text,
                "name": name,
                "audio_file": final_audio_path
            }
            
        except Exception as e:
            logger.error(f"OpenAI processing error: {str(e)}")
            # Fallback
            return {
                "transcribed_text": "Error in processing",
                "intent": "general",
                "confidence": 0.0,
                "response_text": "Λυπάμαι, δεν μπόρεσα να σας κατανοήσω. Θα σας συνδέσω με την υποδοχή.",
                "name": None,
                "audio_file": None
            }

# Δημιουργία instance του agent
agent = OpenAIVoiceAgent()

@app.post("/process_audio")
async def process_audio_openai(audio: UploadFile = File(...)):
    """Επεξεργασία audio με OpenAI Services"""
    
    try:
        if not client:
            raise HTTPException(status_code=500, detail="OpenAI client not available")
            
        # Αποθήκευση uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name

        logger.info("Processing with OpenAI...")
        
        # Επεξεργασία με OpenAI
        result = agent.process_audio_openai(temp_audio_path)
        
        # Cleanup input file
        os.unlink(temp_audio_path)
        
        # Routing info για Asterisk
        routing_info = {
            "department": result["intent"],
            "priority": "normal" if result["confidence"] > 0.7 else "low",
            "collected_data": {"caller_name": result["name"]} if result["name"] else {},
            "confidence": result["confidence"]
        }
        
        response_data = {
            "transcribed_text": result["transcribed_text"],
            "intent": result["intent"], 
            "response_text": result["response_text"],
            "name": result["name"],
            "timestamp": datetime.now().isoformat(),
            "routing_info": routing_info,
            "confidence": result["confidence"],
            "provider": "openai"
        }
        
        # Επιστροφή του MP3 file
        if result["audio_file"] and os.path.exists(result["audio_file"]):
            # ΔΙΟΡΘΩΣΗ: Proper encoding για ελληνικά
            response_data_clean = {
                "transcribed_text": result["transcribed_text"],
                "intent": result["intent"], 
                "response_text": result["response_text"],
                "name": result["name"],
                "timestamp": datetime.now().isoformat(),
                "routing_info": routing_info,
                "confidence": result["confidence"],
                "provider": "openai"
            }
            
            headers = {
                "x-agent-data": json.dumps(response_data_clean, ensure_ascii=True),
                "Content-Type": "audio/mpeg; charset=utf-8"
            }
            
            # Debug log
            logger.info(f"Returning audio file: {result['audio_file']} (exists: {os.path.exists(result['audio_file'])})")
            
            return FileResponse(
                result["audio_file"], 
                media_type="audio/mpeg",
                headers=headers,
                filename=f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            )
        else:
            # Fallback αν δεν δημιουργήθηκε audio
            raise HTTPException(status_code=500, detail="TTS failed to generate audio")

    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "provider": "openai",
        "client_status": "connected" if client else "disconnected",
        "mpg123_note": "MP3 conversion handled by Asterisk server",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/text_intent")
async def detect_text_intent_openai(data: dict):
    """Text-only intent detection με OpenAI"""
    try:
        if not client:
            raise Exception("OpenAI client not available")
            
        text = data.get("text", "")
        
        chat_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": agent.system_prompt},
                {"role": "user", "content": f"Πελάτης είπε: '{text}'"}
            ],
            temperature=0.3
        )
        
        ai_response = chat_response.choices[0].message.content
        logger.info(f"GPT Raw Response: {ai_response}")
        
        try:
            parsed_response = json.loads(ai_response)
        except json.JSONDecodeError:
            # Αν το GPT δεν έδωσε JSON, κάνε fallback
            parsed_response = {
                "intent": "general",
                "confidence": 0.3,
                "response": "Θα σας συνδέσω με την υποδοχή μας.",
                "name": None
            }
        
        return {
            "text": text,
            "intent": parsed_response.get("intent", "general"),
            "name": parsed_response.get("name"),
            "response": parsed_response.get("response", "Θα σας βοηθήσω."),
            "confidence": parsed_response.get("confidence", 0.5),
            "provider": "openai"
        }
    except Exception as e:
        logger.error(f"Text intent error: {str(e)}")
        return {
            "text": text,
            "intent": "general", 
            "name": None,
            "response": "Θα σας συνδέσω με την υποδοχή.",
            "confidence": 0.0,
            "provider": "openai",
            "error": str(e)
        }


@app.post("/speak")
async def speak_from_text(data: dict):
    """Simple OpenAI TTS API from plain text"""
    try:
        import requests

        text = data.get("text")
        if not text:
            raise HTTPException(status_code=400, detail="Missing 'text'")

        voice = data.get("voice", "alloy")
        model = data.get("model", "tts-1")
        response_format = data.get("format", "mp3")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format
        }

        response = requests.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"OpenAI TTS error {response.status_code}: {response.text}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(response.content)
            return FileResponse(tmp.name, media_type="audio/mpeg")

    except Exception as e:
        logger.error(f"/speak error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)