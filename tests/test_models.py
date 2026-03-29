import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    raise RuntimeError('GEMINI_API_KEY not found. Set it in your .env file.')

import warnings
warnings.filterwarnings('ignore')

import google.generativeai as genai

try:
    genai.configure(api_key=api_key)
    models = genai.list_models()
    
    print('Available models for generateContent:')
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f'  {model.name}')
except Exception as e:
    print(f'Error listing models: {str(e)}')
