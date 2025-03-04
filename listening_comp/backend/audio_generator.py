import os
import boto3
import subprocess
from pathlib import Path

class AudioGenerator:
    def __init__(self):
        self.polly = boto3.client('polly')
        self.audio_dir = os.path.join(os.path.dirname(__file__), "data", "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Updated voice mapping with distinct voices
        self.voices = {
            'announcer': 'Takumi',  # Male voice for announcer
            'male': 'Kazuha',       # Different male voice
            'female': 'Mizuki'      # Female voice
        }

    def _generate_audio_segment(self, text, voice, output_path):
        response = self.polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice,
            LanguageCode='ja-JP',
            Engine='neural'  # Explicitly specify neural engine
        )
        with open(output_path, 'wb') as file:
            file.write(response['AudioStream'].read())

    def _combine_audio_files(self, files, output_path):
        # Create a temporary file with list of files to combine
        list_file = os.path.join(self.audio_dir, 'filelist.txt')
        with open(list_file, 'w') as f:
            for file in files:
                f.write(f"file '{file}'\n")
        
        # Use ffmpeg to combine audio files
        subprocess.run([
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            output_path
        ])
        
        # Clean up temporary files
        os.remove(list_file)
        for file in files:
            os.remove(file)

    def generate_question_audio(self, question, question_id):
        try:
            # Generate audio segments
            temp_files = []
            
            # 1. Introduction
            intro_file = os.path.join(self.audio_dir, f'temp_intro_{question_id}.mp3')
            self._generate_audio_segment(
                question['introduction'],
                self.voices['announcer'],
                intro_file
            )
            temp_files.append(intro_file)
            
            # 2. Conversation
            conv_file = os.path.join(self.audio_dir, f'temp_conv_{question_id}.mp3')
            self._generate_audio_segment(
                question['conversation'],
                self.voices['male'] if '男の人' in question['conversation'] else self.voices['female'],
                conv_file
            )
            temp_files.append(conv_file)
            
            # 3. Question
            question_file = os.path.join(self.audio_dir, f'temp_question_{question_id}.mp3')
            self._generate_audio_segment(
                question['question'],
                self.voices['announcer'],
                question_file
            )
            temp_files.append(question_file)
            
            # Combine audio files
            output_file = os.path.join(self.audio_dir, f'question_{question_id}.mpeg')
            self._combine_audio_files(temp_files, output_file)
            
            return output_file
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return None