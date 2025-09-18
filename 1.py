import sounddevice as sd
import numpy as np
import wavio
import time
import os
import threading
from collections import deque

# --- Configuration ---
RECORD_DURATION_SECONDS = 30
OVERLAP_SECONDS = 15
SAMPLE_RATE = 44100  # samples per second
CHANNELS = 1         # mono audio
AUDIO_FORMAT = 'wav'
OUTPUT_DIR = 'recordings'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# A deque to store the recorded audio filenames that are ready to be processed/sent
audio_queue = deque()
recording_active = True

def record_audio_segment(filename, duration, samplerate, channels):
    """Records audio for a specified duration and saves it to a file."""
    print(f"Recording to {filename} for {duration} seconds...")
    try:
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16')
        sd.wait()  # Wait until recording is finished
        wavio.write(filename, recording, samplerate, sampwidth=2) # sampwidth=2 for 16-bit audio
        print(f"Finished recording {filename}")
        audio_queue.append(filename) # Add filename to the queue for processing
    except Exception as e:
        print(f"Error during recording to {filename}: {e}")

def continuous_recorder():
    """Manages continuous, overlapping audio recording."""
    segment_counter = 0
    start_time = time.time()

    while recording_active:
        current_time = time.time()
        # Calculate when the next recording should start based on overlap
        # Each new recording starts OVERLAP_SECONDS after the previous one.
        # So, if first recording started at t=0, next starts at t=15, then t=30 etc.
        next_record_start_offset = segment_counter * OVERLAP_SECONDS
        time_until_next_record = next_record_start_offset - (current_time - start_time)

        if time_until_next_record <= 0:
            filename = os.path.join(OUTPUT_DIR, f'audio_segment_{segment_counter:04d}.{AUDIO_FORMAT}')
            
            # Start recording in a new thread to not block the main loop
            record_thread = threading.Thread(
                target=record_audio_segment,
                args=(filename, RECORD_DURATION_SECONDS, SAMPLE_RATE, CHANNELS)
            )
            record_thread.start()
            segment_counter += 1
            # Adjust start_time for the next iteration if the recording took longer
            # than expected, or just let it calculate from the absolute start_time
            # For simplicity, we'll let it naturally drift, or you can force alignment:
            # start_time = current_time # if you want exact 15s intervals from *now*
        
        # Sleep for a short period to avoid busy-waiting
        time.sleep(0.1)

# --- Start the recorder in a separate thread ---
# recorder_thread = threading.Thread(target=continuous_recorder)
# recorder_thread.start()
# print("Continuous recorder started. Press Ctrl+C to stop.")

# # Keep the main thread alive for a bit to see recordings start
# try:
#     while True:
#         time.sleep(1)
# except KeyboardInterrupt:
#     recording_active = False
#     print("Stopping recorder...")
#     recorder_thread.join()
#     print("Recorder stopped.")
