from flask import Flask, render_template, request, jsonify
import os
import time
from pydub import AudioSegment 
import whisper
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import io
import base64
import speech_recognition as sr

# Initialize Flask app and Whisper model
app = Flask(__name__)
model_whisper = whisper.load_model("base")

# Filler words for fluency analysis
FILLER_WORDS = ['um', 'uh', 'like', 'you know', 'actually', 'basically']

# Save recorded audio
def save_audio(file_path="recorded_audio.wav"):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.listen(source)
        with open(file_path, "wb") as f:
            f.write(audio_data.get_wav_data())
        return file_path
    except Exception as e:
        return None

# Convert and process uploaded audio
def process_audio(audio_path):
    # Convert to WAV if needed
    if not audio_path.endswith('.wav'):
        audio = AudioSegment.from_file(audio_path)
        audio_path = audio_path.rsplit('.', 1)[0] + '.wav'
        audio.export(audio_path, format="wav")
    
    # Transcription
    start_time = time.time()
    result = model_whisper.transcribe(audio_path)
    text = result["text"]
    elapsed_time = time.time() - start_time

    # Calculate WPM
    words = text.split()
    word_count = len(words)
    wpm = (word_count / elapsed_time) * 60

    # Filler word analysis
    filler_count = sum(1 for word in words if word.lower() in FILLER_WORDS)
    filler_word_list = [word for word in words if word.lower() in FILLER_WORDS]

    # Generate warnings
    warnings = []
    if filler_count > 5:  # Adjust threshold as needed
        warnings.append("High number of filler words detected.")
    if wpm < 80:  # Adjust threshold as needed
        warnings.append("Speaking too slowly. Try to increase your pace.")
    if wpm > 180:
        warnings.append("Speaking too quickly. Consider slowing down for clarity.")

    return {
        "text": text,
        "wpm": wpm,
        "filler_count": filler_count,
        "filler_words": filler_word_list,
        "warnings": warnings
    }


def create_wordcloud(text, stopwords=STOPWORDS, video_id=None, channel_title=None):
    if not text.strip() or len(text.split()) == 0:
        return None  # Handle empty or invalid text
    
    # Generate word cloud
    wordcloud = WordCloud(
        max_font_size=50,
        min_font_size=10,
        max_words=100,
        prefer_horizontal=1,
        background_color="white",
        stopwords=stopwords,
        scale=2.0,
        collocations=False
    ).generate(text)

    # Save to a BytesIO object
    # img_io = io.BytesIO()
    # wordcloud.to_image().save(img_io, format="PNG")
    # img_io.seek(0)

    # # Convert to base64
    # img_base64 = base64.b64encode(img_io.getvalue()).decode("utf-8")
    # return img_base64


@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/speech", methods=["GET", "POST"])
def speech():
    if request.method == "POST":
        # Handle uploaded audio file
        audio_file = request.files["audio"]
        file_path = os.path.join("static", "uploads", audio_file.filename)
        audio_file.save(file_path)
        
        # Process and analyze audio
        analysis = process_audio(file_path)
        text = analysis["text"]
        # wordcloud_image = create_wordcloud(text)

        
        return jsonify({
            "text": analysis["text"],
            "wpm": analysis["wpm"],
            "filler_count": analysis["filler_count"],
            "filler_words": analysis["filler_words"],
            # "wordcloud_image": wordcloud_image,
            "warnings": analysis["warnings"]
        })

    return render_template("speech.html")

@app.route("/chart.html", methods=["GET"])
def chart():
    # This should get the text and generate wordcloud
    text = request.args.get('text', '')
    wordcloud_image = create_wordcloud(text)
    return render_template("chart.html", wordcloud_image=wordcloud_image, text=text)



if __name__ == "__main__":
    app.run(debug=True)
