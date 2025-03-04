from audio_generator import AudioGenerator

def test_audio_generation():
    generator = AudioGenerator()
    
    sample_question = {
        'introduction': 'これはテストの紹介です',
        'conversation': '男の人: こんにちは\n女の人: こんにちは',
        'question': 'これは何についての会話ですか？'
    }
    
    audio_file = generator.generate_question_audio(sample_question, 1)
    print(f"Generated audio file: {audio_file}")

if __name__ == "__main__":
    test_audio_generation()