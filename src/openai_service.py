import os
import json
from openai import OpenAI

class OpenAIService:
    """Service for interacting with OpenAI APIs."""
    
    # Available speech-to-text models
    WHISPER_MODELS = [
        "whisper-1",
        "whisper-large-v3",
        "gpt-4o-transcribe",
        "gpt-4o-mini-transcribe"
    ]
    
    # Available text models for cleaning and title generation
    TEXT_MODELS = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-3.5-turbo"
    ]
    
    def __init__(self, api_key=""):
        """Initialize the OpenAI service with the provided API key."""
        self.api_key = api_key
        self.client = None
        if api_key:
            self.set_api_key(api_key)
    
    def set_api_key(self, api_key):
        """Set or update the API key and reinitialize the client."""
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    
    def get_available_whisper_models(self):
        """Get a list of available Whisper models."""
        return self.WHISPER_MODELS
    
    def get_available_text_models(self):
        """Get a list of available text models for cleaning and title generation."""
        return self.TEXT_MODELS
    
    def transcribe_audio(self, file_path, model="whisper-1"):
        """
        Transcribe an audio file using OpenAI's Whisper API.
        
        Args:
            file_path (str): Path to the audio file to transcribe
            model (str): The model to use for transcription
            
        Returns:
            str: The transcribed text
        
        Raises:
            Exception: If there's an error during transcription
        """
        if not self.client:
            raise Exception("API key not set. Please set your OpenAI API key in settings.")
        
        try:
            # For GPT-4o transcribe models, use the chat completions API with audio input
            if model.startswith("gpt-4o") and "transcribe" in model:
                with open(file_path, "rb") as audio_file:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant that transcribes audio accurately. Provide only the transcription without any additional commentary."},
                            {"role": "user", "content": [
                                {"type": "audio", "audio": audio_file.read()}
                            ]}
                        ],
                        response_format={"type": "text"}
                    )
                    return response.choices[0].message.content
            # For traditional Whisper models, use the audio transcriptions API
            else:
                with open(file_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=model,
                        file=audio_file
                    )
                    return response.text
        except Exception as e:
            raise Exception(f"Error transcribing audio: {str(e)}")
    
    def clean_text(self, text, model="gpt-4o-mini"):
        """
        Clean up transcribed text using specified model.
        
        Args:
            text (str): The transcribed text to clean
            model (str): The model to use for cleaning
            
        Returns:
            str: The cleaned text
            
        Raises:
            Exception: If there's an error during text cleaning
        """
        if not self.client:
            raise Exception("API key not set. Please set your OpenAI API key in settings.")
        
        try:
            system_prompt = """You are a text rewriting assistant. You will receive text that was captured and transcribed from speech to text processing. Your task is to edit this text for intelligibility and clarity. You should resolve any obvious typos. If you can identify in the text instructions to remove part of the transcribed text, such as "actually, delete that" Then you should action the intent, which you can infer from the instruction which was included in the transcript. You should also add paragraph spacing. You should use bullet points where it would be helpful to improve the intelligibility of the text. You should add headers where it would similarly make the text more readable. If there is repetition or redundancy in the text, then you can remove it in your improved version. Once you have applied these edits, you must return the edited text."""
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "text"}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error cleaning text: {str(e)}")
    
    def generate_title(self, text, model="gpt-4o-mini"):
        """
        Generate a title and filename for the transcribed text.
        
        Args:
            text (str): The transcribed text
            model (str): The model to use for title generation
            
        Returns:
            tuple: (title, filename)
            
        Raises:
            Exception: If there's an error during title generation
        """
        if not self.client:
            raise Exception("API key not set. Please set your OpenAI API key in settings.")
        
        try:
            system_prompt = """You are a helpful assistant. Your task is to generate a short title for the text. The title should summarize its main content. In addition to the display title, you must also generate a suggested file name. The file name should be similar to the main title, but it should be written in kebab case (no upper case, hyphens for space). Return your response in JSON format with two fields: 'title' and 'filename'."""
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("title", "Untitled"), result.get("filename", "untitled")
        except Exception as e:
            raise Exception(f"Error generating title: {str(e)}")
