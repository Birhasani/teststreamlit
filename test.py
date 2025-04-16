import streamlit as st
import pyttsx3
from gtts import gTTS
import os
import tempfile

# Function for pyttsx3 TTS
def pyttsx3_text_to_speech(text):
    # Initialize pyttsx3 engine
    engine = pyttsx3.init()

    # Set voice to Bahasa Indonesia
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'indonesian' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break

    engine.setProperty('rate', 150)  # Adjust speech rate
    engine.setProperty('volume', 1)  # Set volume (0.0 to 1.0)

    # Save audio to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    engine.save_to_file(text, temp_file.name)
    engine.runAndWait()

    return temp_file.name

# Function for gTTS TTS
def gtts_text_to_speech(text):
    # Create TTS object with Bahasa Indonesia
    tts = gTTS(text=text, lang='id')

    # Save the speech to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)

    return temp_file.name

# Streamlit UI
st.title("Text to Speech with pyttsx3 and gTTS")

text = st.text_area("Enter Text to Convert to Speech", "Selamat datang di aplikasi kami!")

st.write("Select TTS Engine")
tts_choice = st.radio("Choose TTS Engine", ('pyttsx3', 'gTTS'))

if tts_choice == 'pyttsx3':
    st.write("Generating Speech with pyttsx3...")
    audio_file_path = pyttsx3_text_to_speech(text)
    st.audio(audio_file_path, format="audio/mp3")
elif tts_choice == 'gTTS':
    st.write("Generating Speech with gTTS...")
    audio_file_path = gtts_text_to_speech(text)
    st.audio(audio_file_path, format="audio/mp3")

