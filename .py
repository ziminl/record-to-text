import sounddevice as sd
import numpy as np
import wavio
import time
import os
import threading
import speech_recognition as sr
import requests
from collections import deque

RECORD_DURATION_SECONDS = 30
OVERLAP_SECONDS = 15
SAMPLE_RATE = 44100
CHANNELS = 1
AUDIO_FORMAT = 'wav'
OUTPUT_DIR = 'recordings'
DISCORD_WEBHOOK_URL = 'edit this edit this edit this'
os.makedirs(OUTPUT_DIR, exist_ok=True)

audio_queue = deque()
recording_active = True

def record_audio_segment(filename, duration, samplerate, channels):
    print(f"[RECORD] Recording {filename}...")
    try:
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16')
        sd.wait()
        wavio.write(filename, recording, sampwidth=2, rate=samplerate)
        print(f"[RECORD] Saved {filename}")
        audio_queue.append(filename)
    except Exception as e:
        print(f"[RECORD] Error recording audio: {e}")

def continuous_recorder():
    segment_counter = 0
    while recording_active:
        filename = os.path.join(OUTPUT_DIR, f'audio_segment_{segment_counter:04d}.{AUDIO_FORMAT}')
        record_audio_segment(filename, RECORD_DURATION_SECONDS, SAMPLE_RATE, CHANNELS)
        segment_counter += 1
        for _ in range(int(OVERLAP_SECONDS * 10)):
            if not recording_active:
                break
            time.sleep(0.1)

def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            print(f"[TRANSCRIBE] Text: {text}")
            return text
    except sr.UnknownValueError:
        print(f"[TRANSCRIBE] Could not understand audio: {file_path}")
        return None
    except sr.RequestError as e:
        print(f"[TRANSCRIBE] API error: {e}")
        return None
    except Exception as e:
        print(f"[TRANSCRIBE] Error: {e}")
        return None

def send_text_to_discord(webhook_url, content):
    if not content:
        return
    try:
        response = requests.post(webhook_url, json={"content": content})
        if response.status_code == 204:
            print("[DISCORD] Message sent successfully.")
        else:
            print(f"[DISCORD] Failed to send. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"[DISCORD] Error sending message: {e}")

def main():
    global recording_active
    recorder_thread = threading.Thread(target=continuous_recorder, daemon=True)
    recorder_thread.start()
    print("[INFO] Continuous recording started...")
    try:
        while True:
            if audio_queue:
                audio_file = audio_queue.popleft()
                print(f"[PROCESS] Processing {audio_file}...")
                transcribed_text = transcribe_audio(audio_file)
                if transcribed_text:
                    send_text_to_discord(DISCORD_WEBHOOK_URL, f" **Transcript:** {transcribed_text}")
                else:
                    print("[PROCESS] No transcription.")
            else:
                time.sleep(1)
    except KeyboardInterrupt:
        print("[INFO] Keyboard interrupt received. Stopping...")
        recording_active = False
        recorder_thread.join()
        print("[INFO] Recorder thread terminated. Exiting...")

if __name__ == "__main__":
    main()
