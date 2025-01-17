const recordBtn = document.getElementById("record-btn");
const resultsDiv = document.getElementById("analysis-results");

recordBtn.addEventListener("click", () => {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const mediaRecorder = new MediaRecorder(stream);
            const chunks = [];
            mediaRecorder.start();

            recordBtn.textContent = "Recording...";
            mediaRecorder.ondataavailable = e => chunks.push(e.data);

            mediaRecorder.onstop = () => {
                const blob = new Blob(chunks, { type: "audio/wav" });
                const audioFile = new File([blob], "audio.wav", { type: "audio/wav" });

                const formData = new FormData();
                formData.append("audio", audioFile);

                axios.post("/speech", formData)
                    .then(response => {
                        const data = response.data;
                        resultsDiv.innerHTML = `
                            <p><strong>Transcribed Text:</strong> ${data.text}</p>
                            <p><strong>Words per Minute:</strong> ${data.wpm.toFixed(2)}</p>
                            <p><strong>Filler Words:</strong> ${data.filler_words.join(", ")}</p>
                            <p><strong>Filler Word Count:</strong> ${data.filler_count}</p>
                        `;
                    })
                    .catch(err => {
                        resultsDiv.textContent = "Error analyzing speech.";
                    });
            };

            setTimeout(() => mediaRecorder.stop(), 5000); // Stop after 5 seconds
        })
        .catch(err => {
            resultsDiv.textContent = "Microphone access denied.";
        });
});
