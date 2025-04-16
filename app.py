import streamlit as st
import subprocess
from PIL import Image
import easyocr
import numpy as np
from google import genai
import requests
from io import BytesIO
from mongodb_integration.mongo_db import save_to_mongo  # Import MongoDB save function
from gtts import gTTS
import tempfile

class TaraDashboard:
    def __init__(self):
        self.api_key = st.secrets["general"]["api_key"]
        self.google_credentials = st.secrets["general"]["google_application_credentials"]
        self.model_path = "/mount/src/tarabraille/pretrained_model_tts/best_model.pth"
        self.config_path = "/mount/src/tarabraille/pretrained_model_tts/config.json"
        self.output_path = "/mount/src/tarabraille/output.wav"  # Output file untuk suara
        self.speakers_path = "/mount/src/tarabraille/pretrained_model_tts/speakers.pth"  # Path speakers
        self.client = genai.Client(api_key=self.api_key)  # Inisialisasi Gemini API Client

        # Inisialisasi EasyOCR Reader untuk Bahasa Indonesia dan Bahasa Inggris
        self.reader = easyocr.Reader(['en', 'id'])  # Menambahkan lebih banyak bahasa jika perlu
        self.ESP32_URL = "http://<ESP32_IP>:80/braille"  # Replace with your actual ESP32 IP

    def fixed_text(self, input_text):
        """Memperbaiki teks menggunakan Gemini API"""
        chat = self.client.chats.create(model="gemini-2.0-flash")
        response = chat.send_message(f"Coba rapikan teksnya apabila ada yang salah tolong perbaiki katanya (selalu dalam bahasa indonesia kecuali apabila memang istilah asing) dengan langsung tanpa kata pengantar dan penutup dari kamu: {input_text}")
        return response.text
    
    def detect_text_from_image(self, image):
        """Deteksi teks dari gambar menggunakan EasyOCR"""
        image_np = np.array(image)
        result = self.reader.readtext(image_np)
        detected_text = " ".join([text[1] for text in result])
        detected_text = self.fixed_text(detected_text)
        return detected_text if detected_text else ""

    def convert_char_to_binary(self, char):
        """Extended Braille Map to include numbers, symbols, and math"""
        braille_map = {
            'a': '10000000', 'b': '11000000', 'c': '10100000', 'd': '10110000', 'e': '10010000', 
            'f': '11100000', 'g': '11110000', 'h': '11010000', 'i': '01100000', 'j': '01110000', 
            'k': '10000100', 'l': '11000100', 'm': '10100100', 'n': '10110100', 'o': '10010100',
            'p': '11100100', 'q': '11110100', 'r': '11010100', 's': '01100100', 't': '01110100',
            'u': '10000110', 'v': '11000110', 'w': '01110010', 'x': '10100110', 'y': '10110110', 
            'z': '10010110', ' ': '00000000',

            # Numbers (precedes with the number sign ⠼)
            '0': '01110111', '1': '10000001', '2': '11000001', '3': '10100001', '4': '10110001', 
            '5': '10010001', '6': '11100001', '7': '11110001', '8': '11010001', '9': '01100001',

            # Punctuation
            '.': '01001110', ',': '01000010', '?': '01100111', '!': '01101101', ':': '01011010', 
            ';': '01101010', '"': '01000001', "'": '01000101',

            # Mathematical Operators
            '+': '01000011', '-': '00101100', '=': '01100011', '/': '01001011', '*': '00101011', 
            '%': '01110101', '$': '01011100', '(': '00111000', ')': '00111001', '&': '01000000',

            # Common symbols
            '@': '01000010', '#': '01101000', '$': '01011100', '^': '01011101', '{': '01110000',
            '}': '01110001', '[': '01110010', ']': '01110011', '\\': '00111100', '_': '00111101', 
            '|': '01011110'
        }
        return braille_map.get(char, None)

    def convert_text_to_braille_binary(self, text):
        braille = []
        for char in text.lower():
            pattern = self.convert_char_to_binary(char)
            if pattern:
                braille.append(pattern)
        return ' '.join(braille)

    def summarize_text(self, input_text):
        chat = self.client.chats.create(model="gemini-2.0-flash")
        response = chat.send_message(f"Coba ringkas dengan bahasa yang baik dan benar agar mudah dipahami dan menjadi pengetahuan yang utuh langsung tanpa kata pengantar dari kamu: {input_text}")
        return response.text

    # Fungsi untuk mengonversi teks menjadi suara menggunakan gTTS
    def convert_text_to_speech(self, summarized_text):
        # Buat objek gTTS dengan bahasa Indonesia
        tts = gTTS(text=summarized_text, lang='id')
        
        # Simpan hasil suara ke file sementara
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        
        # Kembalikan path file suara sementara yang sudah disimpan
        return temp_file.name

    def run(self):
        """Menjalankan aplikasi Streamlit"""
        if "page" not in st.session_state:
            st.session_state.page = "Landing Page"  # Default page
        
        page = st.sidebar.radio("Pilih Halaman", ["Landing Page", "Image to Text & Braille", "Text Editing & Summarizing"], index=["Landing Page", "Image to Text & Braille", "Text Editing & Summarizing"].index(st.session_state.page))

        if page == "Landing Page":
            self.landing_page()
        elif page == "Image to Text & Braille":
            self.image_to_text_braille_page()
        elif page == "Text Editing & Summarizing":
            self.text_editing_summarizing_page()

    def landing_page(self):
        st.title("Selamat Datang di Tara Dashboard")
        st.markdown("""
                    Proyek ini bertujuan untuk membantu siswa tunanetra dalam proses pembelajaran berbasis IoT.
                      Gambar yang diinput akan diproses secara otomatis menjadi:

                      - 🧠 Teks melalui AI Image to Text
                      - 📝 Ringkasan otomatis (Text to Summary)
                      - 🔈 Suara (Text to Voice)
                      - ⠿ Konversi ke Braille 2x4
                    """)
        st.success("Silakan lanjut ke Dashboard 2 untuk memulai.")
        st.write("Klik tombol 'Lanjut' untuk melanjutkan ke halaman berikutnya.")
        if st.button("Lanjut"):
            st.session_state.page = "Image to Text & Braille"  # Set next page

    def image_to_text_braille_page(self):
        st.title("Konversi Gambar ke Teks dan Braille")
        
        # Initialize image variable to None
        image = None

        # Option 1: File upload (Drag-and-Drop)
        uploaded_image = st.file_uploader("Upload Image (Drag and Drop)", type=["png", "jpg", "jpeg"])
        
        # Option 2: Camera input (Take a picture)
        captured_image = st.camera_input("Take a Picture")

        # Handle the case if either the uploaded image or captured image is provided
        if uploaded_image is not None:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Image", use_container_width=True)
        elif captured_image is not None:
            # If a picture is taken, load the image from the captured data
            image = Image.open(captured_image)
            st.image(image, caption="Captured Image", use_container_width=True)

        if image is not None:
            with st.spinner("Processing Image..."):
                detected_text = self.detect_text_from_image(image)
            
            if detected_text:
                # Save detected text and Braille text in session state
                st.session_state.detected_text = detected_text
                braille_text = self.convert_text_to_braille_binary(detected_text)
                st.session_state.braille_text = braille_text

                st.write("Detected Text from Image:")
                st.write(detected_text)
                st.write("Braille Representation:")
                st.text(braille_text)  # Menampilkan teks Braille

                if st.button("Send Braille to Board"):
                    # Send Braille string to ESP32 via HTTP
                    response = requests.get(self.ESP32_URL, params={"braille": braille_text})
                    st.write("Response from ESP32:", response.text)

                if st.button("Lanjut"):
                    # Save image, Braille, and detected text to MongoDB
                    data = {
                        "image": uploaded_image.read() if uploaded_image else captured_image.getvalue(),  # Save image as binary
                        "braille": braille_text,
                        "detected_text": detected_text
                    }
                    save_to_mongo(data)  # Save to MongoDB
                    st.session_state.page = "Text Editing & Summarizing"  # Set next page
            else:
                st.warning("No text detected in the image.")
        else:
            st.warning("Please upload an image or take a picture.")


    def text_editing_summarizing_page(self):
        st.title("Edit Teks, Ringkasan, dan Konversi ke Suara")
        st.write("Edit teks yang terdeteksi dari gambar.")

        uploaded_text = st.text_area("Teks yang terdeteksi", st.session_state.get("detected_text", ""), height=200)

        if uploaded_text:
            st.session_state.edited_text = uploaded_text  # Save edited text

            summarized_text = self.summarize_text(uploaded_text)
            st.session_state.summarized_text = summarized_text  # Save summarized text

            st.write("Summarized Text:")
            st.write(summarized_text)

            # Pilih suara
            if st.button("Convert to Speech"):
                # Menggunakan gTTS untuk mengonversi teks menjadi suara
                audio_file_path = self.convert_text_to_speech(summarized_text)
                st.audio(audio_file_path, format="audio/mp3")  # Memutar suara di Streamlit

if __name__ == "__main__":
    dashboard = TaraDashboard()  # Membuat objek TaraDashboard
    dashboard.run()  # Menjalankan aplikasi
