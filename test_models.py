import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyAxa9KJlmH_OTLSKcqBYEblPlwiPqWcKq0'

import warnings
warnings.filterwarnings('ignore')

import google.generativeai as genai

try:
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    models = genai.list_models()
    
    print('Available models for generateContent:')
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f'  {model.name}')
except Exception as e:
    print(f'Error listing models: {str(e)}')
