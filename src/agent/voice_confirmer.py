"""
Voice confirmation system using OpenAI Whisper (STT) and TTS APIs.
Chained architecture for reliable yes/no detection.
"""

import os
import tempfile
import time
from typing import Optional
from openai import OpenAI
import sounddevice as sd
import numpy as np
import wave
from pathlib import Path


class VoiceConfirmer:
    """Chained voice confirmation using Whisper + TTS"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.enabled = os.getenv("VOICE_CONFIRMATION_ENABLED", "false").lower() == "true"
        self.timeout = int(os.getenv("VOICE_CONFIRMATION_TIMEOUT", "5"))
        self.default_response = os.getenv("VOICE_DEFAULT_RESPONSE", "no").lower()
        
        # Audio settings
        self.sample_rate = 16000  # 16kHz is standard for speech
        self.channels = 1  # Mono
        
        # Create temp directory for audio files
        self.temp_dir = Path(tempfile.gettempdir()) / "mindaware_voice"
        self.temp_dir.mkdir(exist_ok=True)
        
        print(f"[VOICE] Initialized - Enabled: {self.enabled}, Timeout: {self.timeout}s")
    
    def inform_pilot(self, action: str, context: dict):
        """
        Inform pilot about automatic action (no confirmation needed).
        Used for takeoff when all parameters are good.
        
        Args:
            action: "takeoff"
            context: cognitive_state dict for context
        """
        if not self.enabled:
            return
        
        try:
            question = self._generate_question(action, context)
            print(f"[VOICE] Announcing: {question}")
            self._speak(question)
        except Exception as e:
            print(f"[VOICE] Error during announcement: {e}")
    
    def ask_confirmation(self, action: str, context: dict) -> bool:
        """
        Ask user for voice confirmation.
        
        Args:
            action: "takeoff" or "land" or "turn_around"
            context: cognitive_state dict for context
        
        Returns:
            True if confirmed, False otherwise
        """
        if not self.enabled:
            print("[VOICE] Voice confirmation disabled - auto-confirming")
            return True
        
        try:
            # Step 1: Generate question based on action
            question = self._generate_question(action, context)
            print(f"[VOICE] Question: {question}")
            
            # Step 2: Speak the question (TTS)
            self._speak(question)
            
            # Step 3: Listen for response (record audio)
            print(f"[VOICE] Listening for {self.timeout} seconds...")
            audio_data = self._record_audio(duration=self.timeout)
            
            if audio_data is None:
                print("[VOICE] No audio recorded - using default response")
                return self.default_response == "yes"
            
            # Step 4: Transcribe response (Whisper)
            transcription = self._transcribe(audio_data)
            print(f"[VOICE] Transcription: '{transcription}'")
            
            # Step 5: Parse yes/no
            confirmed = self._parse_response(transcription)
            
            return confirmed
        
        except Exception as e:
            print(f"[VOICE] Error during confirmation: {e}")
            print(f"[VOICE] Falling back to default: {self.default_response}")
            return self.default_response == "yes"
    
    def _generate_question(self, action: str, context: dict) -> str:
        """Generate contextual question based on action and cognitive state"""
        focus = context.get('focus', 0.5)
        fatigue = context.get('fatigue', 0.5)
        overload = context.get('overload', 0.5)
        stress = context.get('stress', 0.5)
        
        if action == "takeoff":
            # Informational only - automatic takeoff
            return (f"Your cognitive state is optimal with focus at {focus:.1f}. "
                   f"All parameters are good. Taking the drone up to 1 meter now.")
        elif action == "land":
            # Always ask for confirmation before landing
            return (f"I detect critical cognitive state with fatigue at {fatigue:.1f} "
                   f"and stress at {stress:.1f}. All parameters are concerning. "
                   f"Should I land the drone immediately? Say yes or no.")
        elif action == "turn_around":
            return (f"Cognitive state is mixed. Should I rotate the drone 180 degrees? "
                   f"Say yes or no.")
        else:
            return f"Should I {action}? Say yes or no."
    
    def _speak(self, text: str):
        """Use OpenAI TTS API to speak the question"""
        try:
            response = self.client.audio.speech.create(
                model="tts-1",  # Standard TTS model (tts-1-hd for higher quality)
                voice="alloy",  # Clear, neutral voice
                input=text,
                speed=1.1  # Slightly faster for urgency
            )
            
            # Save to temp file
            speech_file = self.temp_dir / f"question_{int(time.time())}.mp3"
            response.stream_to_file(str(speech_file))
            
            # Play the audio file
            self._play_audio_file(speech_file)
            
            # Clean up
            speech_file.unlink(missing_ok=True)
            
        except Exception as e:
            print(f"[VOICE] Error generating speech: {e}")
            # Fall through - recording will still work
    
    def _play_audio_file(self, audio_file: Path):
        """Play an audio file using system tools"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", str(audio_file)], check=True)
            elif system == "Linux":
                # Try multiple players
                for player in ["aplay", "paplay", "ffplay"]:
                    try:
                        subprocess.run([player, str(audio_file)], 
                                     check=True, 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
            elif system == "Windows":
                # Use Windows Media Player
                os.startfile(str(audio_file))
                time.sleep(2)  # Give it time to play
            
        except Exception as e:
            print(f"[VOICE] Error playing audio: {e}")
    
    def _record_audio(self, duration: int) -> Optional[bytes]:
        """
        Record audio from microphone for specified duration.
        
        Args:
            duration: Recording duration in seconds
        
        Returns:
            Audio data as bytes in WAV format, or None if failed
        """
        try:
            print(f"[VOICE] 🎤 Recording started... Speak now!")
            
            # Record audio
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16
            )
            sd.wait()  # Wait until recording is finished
            
            print("[VOICE] Recording complete")
            
            # Convert to WAV format in memory
            wav_file = self.temp_dir / f"response_{int(time.time())}.wav"
            
            with wave.open(str(wav_file), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(self.sample_rate)
                wf.writeframes(recording.tobytes())
            
            # Read back as bytes
            with open(wav_file, 'rb') as f:
                audio_bytes = f.read()
            
            # Clean up
            wav_file.unlink(missing_ok=True)
            
            return audio_bytes
        
        except Exception as e:
            print(f"[VOICE] Error recording audio: {e}")
            return None
    
    def _transcribe(self, audio_data: bytes) -> str:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_data: Audio bytes in WAV format
        
        Returns:
            Transcribed text (lowercase)
        """
        try:
            # Save to temp file for API upload
            temp_file = self.temp_dir / f"transcribe_{int(time.time())}.wav"
            
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            
            # Transcribe using Whisper
            with open(temp_file, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en",
                    response_format="text"
                )
            
            # Clean up
            temp_file.unlink(missing_ok=True)
            
            # Return lowercase for easier parsing
            if isinstance(transcription, str):
                return transcription.lower().strip()
            else:
                return transcription.text.lower().strip()
        
        except Exception as e:
            print(f"[VOICE] Error transcribing audio: {e}")
            return ""
    
    def _parse_response(self, text: str) -> bool:
        """
        Parse yes/no from transcription.
        
        Args:
            text: Transcribed text (lowercase)
        
        Returns:
            True for affirmative, False for negative or unclear
        """
        text = text.lower().strip()
        
        # Empty response
        if not text:
            print(f"[VOICE] Empty response - defaulting to {self.default_response.upper()}")
            return self.default_response == "yes"
        
        # Remove punctuation and convert to words
        import string
        words = [word.strip(string.punctuation) for word in text.split()]
        
        # Affirmative words
        affirmative = ["yes", "yeah", "yep", "sure", "okay", "ok", "yup", 
                      "confirm", "proceed", "affirmative", "correct"]
        
        # Negative words
        negative = ["no", "nope", "cancel", "stop", "don't", "abort", 
                   "negative", "wait", "hold"]
        
        # Check for affirmative (exact word match)
        if any(word in affirmative for word in words):
            print(f"[VOICE] ✅ Confirmed: '{text}'")
            return True
        
        # Check for negative (exact word match)
        if any(word in negative for word in words):
            print(f"[VOICE] ❌ Denied: '{text}'")
            return False
        
        # Check for multi-word phrases
        if "go ahead" in text:
            print(f"[VOICE] ✅ Confirmed: '{text}'")
            return True
        
        # Unclear response - default to NO for safety
        print(f"[VOICE] ⚠️ Unclear response: '{text}' - defaulting to {self.default_response.upper()}")
        return self.default_response == "yes"
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            for file in self.temp_dir.glob("*"):
                file.unlink(missing_ok=True)
        except Exception as e:
            print(f"[VOICE] Error cleaning up temp files: {e}")

