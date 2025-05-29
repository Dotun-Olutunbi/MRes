#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

import os
import time
import wave
import struct
import numpy as np
import requests
import json
import traceback

class WhisperTranscriber:
    def __init__(self, device="default", duration=5):
        self.device = device
        self.duration = duration  # seconds per chunk
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("Please set OPENAI_API_KEY in your environment")

    def check_audio_level(self, wav_file):
        """Check if audio level is above threshold"""
        try:
            wf = wave.open(wav_file, 'rb')
            try:
                # Get audio parameters
                n_channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                n_frames = wf.getnframes()
                
                # Read all frames
                frames = wf.readframes(n_frames)
                
                # Convert to numpy array
                if sample_width == 2:  # 16-bit audio
                    dtype = np.int16
                else:
                    return False
                
                # Convert to numpy array
                audio_data = np.frombuffer(frames, dtype=dtype)
                
                # Calculate RMS (Root Mean Square) of the audio
                rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
                
                # Threshold for considering audio as valid speech
                threshold = 500  # Adjust this value based on testing
                
                print("[Audio] RMS level:", rms)
                return rms > threshold
            finally:
                wf.close()
                
        except Exception as e:
            print("[Audio] Error checking audio level:", str(e))
            return False

    def transcribe_audio(self):
        """Record and transcribe audio using Whisper"""
        try:
            tmp_file = "/tmp/whisper_chunk.wav"
            
            # Record audio to WAV
            os.system(
                "arecord -D %s -f S16_LE -r 16000 -c 1 -d %d %s" %
                (self.device, self.duration, tmp_file)
            )
            
            # Check if audio level is significant
            if not self.check_audio_level(tmp_file):
                print("[Audio] Audio level too low, skipping transcription")
                try:
                    os.remove(tmp_file)
                except:
                    pass
                return
            
            # Send to Whisper via HTTP
            with open(tmp_file, "rb") as audio:
                files = {
                    "file": ("audio.wav", audio, "audio/wav")
                }
                data = {
                    "model": "whisper-1",
                    "language": "en"
                }
                headers = {
                    "Authorization": "Bearer %s" % self.api_key
                }
                
                print("[Whisper] Sending audio to API...")
                resp = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=30
                )
            
            resp.raise_for_status()
            result = resp.json()
            text = result.get("text", "").strip()
            
            if text:
                print("[Whisper] Transcribed text:", text)
            else:
                print("[Whisper] No text in response")
            
            # Clean up the temporary file
            try:
                os.remove(tmp_file)
            except:
                pass
                
        except Exception as e:
            print("Whisper error:", str(e))
            traceback.print_exc()

def main():
    print("Starting Whisper Desktop Transcriber")
    print("Press Ctrl+C to exit")
    
    transcriber = WhisperTranscriber()
    
    try:
        while True:
            print("\nRecording...")
            transcriber.transcribe_audio()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main() 