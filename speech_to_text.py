import sounddevice as sd
import numpy as np
import whisper
import tempfile
import os
from scipy.io import wavfile
import time

# Initialize Whisper model
print("Loading Whisper model...")
model = whisper.load_model("base")
print("Model loaded successfully!")

# Audio recording parameters
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 0.01  # Adjust this value based on your microphone
SILENCE_DURATION = 5  # seconds of silence to trigger pause
CHUNK_DURATION = 0.1  # seconds per chunk

def is_silence(audio_chunk, threshold=SILENCE_THRESHOLD):
    """Check if the audio chunk is silence."""
    return np.max(np.abs(audio_chunk)) < threshold

def record_audio():
    """Record audio until silence is detected."""
    print("\nListening... (Speak now)")
    
    audio_chunks = []
    silence_counter = 0
    
    def audio_callback(indata, frames, time, status):
        if status:
            print(f"Status: {status}")
        audio_chunks.append(indata.copy())
    
    with sd.InputStream(callback=audio_callback,
                       channels=CHANNELS,
                       samplerate=SAMPLE_RATE):
        while True:
            if len(audio_chunks) > 0:
                if is_silence(audio_chunks[-1]):
                    silence_counter += CHUNK_DURATION
                else:
                    silence_counter = 0
                
                if silence_counter >= SILENCE_DURATION:
                    break
            time.sleep(CHUNK_DURATION)
    
    return np.concatenate(audio_chunks, axis=0)

def save_audio_to_temp(audio_data):
    """Save audio data to a temporary WAV file."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wavfile.write(temp_file.name, SAMPLE_RATE, audio_data)
    return temp_file.name

def transcribe_audio(audio_file):
    """Transcribe audio using Whisper."""
    result = model.transcribe(audio_file)
    return result["text"]

def main():
    print("Speech-to-Text with Whisper")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            # Record audio until silence is detected
            audio_data = record_audio()
            
            if len(audio_data) > 0:
                # Save audio to temporary file
                temp_file = save_audio_to_temp(audio_data)
                
                # Transcribe the audio
                print("\nTranscribing...")
                transcription = transcribe_audio(temp_file)
                
                # Clean up temporary file
                os.unlink(temp_file)
                
                # Print transcription
                print(f"\nTranscription: {transcription}")
                print("\n" + "-"*50)
            
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main() 