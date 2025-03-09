from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import torch
import torchaudio
import io
import numpy as np
import uvicorn
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5ForSpeechToText
from transformers import SpeechT5HifiGan

app = FastAPI()

# Load models
processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
tts_model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts") 
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
stt_model = SpeechT5ForSpeechToText.from_pretrained("microsoft/speecht5_asr")

# Speaker embeddings for TTS (pre-computed)
speaker_embeddings = torch.randn(1, 512)  # This is just a placeholder

@app.post("/tts")
async def text_to_speech(text: str):
    inputs = processor(text=text, return_tensors="pt")
    
    # Generate speech
    speech = tts_model.generate_speech(
        inputs["input_ids"], 
        speaker_embeddings, 
        vocoder=vocoder
    )
    
    # Convert to bytes
    buffer = io.BytesIO()
    torchaudio.save(buffer, speech.unsqueeze(0), 16000, format="wav")
    buffer.seek(0)
    
    return JSONResponse(content={"status": "success"})

@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    contents = await file.read()
    
    # Convert to audio tensor
    buffer = io.BytesIO(contents)
    waveform, sample_rate = torchaudio.load(buffer)
    
    # Resample if needed
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(waveform)
    
    # Process through model
    inputs = processor(audio=waveform.squeeze().numpy(), sampling_rate=16000, return_tensors="pt")
    predicted_ids = stt_model.generate(inputs["input_values"])
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    
    return JSONResponse(content={"transcription": transcription[0]})

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7055)