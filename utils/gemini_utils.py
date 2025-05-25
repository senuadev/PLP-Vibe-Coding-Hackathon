import os
import json
import google.generativeai as genai
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv


# Initialize Gemini model
def init_gemini(api_key):
    """Initialize the Gemini model with the provided API key."""
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        raise Exception(f"Failed to initialize Gemini: {str(e)}")

def process_audio_transaction(audio_file, model, filename=None):
    """Process audio file to extract transaction details using Gemini.
    
    Args:
        audio_file: File-like object or Flask file upload object
        model: Initialized Gemini model
        filename: Optional filename if audio_file doesn't have a filename attribute
    """
    try:
        # Read audio file
        audio_bytes = audio_file.read()
        
        # Get the filename if it exists, otherwise use the provided one
        file_extension = ''
        if hasattr(audio_file, 'filename') and audio_file.filename:
            file_extension = audio_file.filename.lower()
        elif filename:
            file_extension = filename.lower()
            
        # Create a prompt that guides the model to extract transaction details
        prompt = """
        Please analyze the following audio transcription and extract the following transaction details:
        
        Required fields:
        - amount: The transaction amount as a float (e.g., 25.50)
        - transaction_type: Either 'income' or 'expense'
        - description: A brief description of the transaction
        
        Optional fields:
        - category: The transaction category (e.g., 'food', 'transportation')
        - transaction_date: Date in YYYY-MM-DD format (default to today if not specified)
        
        Example input 1:
        "I spent $45.67 on groceries at Walmart today"
        
        Example output 1:
        {
            "amount": 45.67,
            "transaction_type": "expense",
            "description": "Groceries at Walmart",
            "category": "groceries"
        }
        
        Example input 2:
        "I received my salary of $2500 for the month of May"
        
        Example output 2:
        {
            "amount": 2500.0,
            "transaction_type": "income",
            "description": "Monthly salary for May"
        }
        
        Now, please process the following audio transcription:
        """
        
        # Get the current date in case it's needed
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Add the current date to the prompt for context
        prompt += f"\nCurrent date: {current_date}\n"
        
        # Determine MIME type based on file extension
        mime_type = 'audio/mpeg'  # default to MP3
        if file_extension.endswith('.wav'):
            mime_type = 'audio/wav'
        
        # Send the audio data to Gemini for processing
        response = model.generate_content([
            prompt,
            {
                'mime_type': mime_type,
                'data': audio_bytes
            }
        ])
        
        # Extract the response text
        response_text = response.text.strip()
        
        # Clean the response to ensure it's valid JSON
        if response_text.startswith('```json'):
            response_text = response_text[response_text.find('{'):response_text.rfind('}')+1]
        
        # Parse the JSON response
        transaction_data = json.loads(response_text)
        
        # Add default values for optional fields if not present
        if 'transaction_date' not in transaction_data:
            transaction_data['transaction_date'] = current_date
            
        # Ensure required fields are present
        required_fields = ['amount', 'transaction_type', 'description']
        for field in required_fields:
            if field not in transaction_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Convert amount to float if it's a string
        if isinstance(transaction_data['amount'], str):
            transaction_data['amount'] = float(transaction_data['amount'].replace('$', '').replace(',', ''))
        
        # Ensure transaction_type is valid
        if transaction_data['transaction_type'] not in ['income', 'expense']:
            raise ValueError("transaction_type must be either 'income' or 'expense'")
        
        return transaction_data
        
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from Gemini")
    except Exception as e:
        raise Exception(f"Error processing audio with Gemini: {str(e)}")


def process_image_transaction(image_file, model):
    """Process image file to extract transaction details using Gemini.
    
    Args:
        image_file: File-like object containing the image
        model: Initialized Gemini model
    
    Returns:
        dict: Extracted transaction details
    """
    try:
        # Read image file
        image_bytes = image_file.read()
        
        # Create a detailed prompt for image analysis
        prompt = """
        Analyze the following receipt image and extract transaction details:
        
        Required fields:
        - amount: The transaction amount as a float (e.g., 25.50)
        - transaction_type: Either 'income' or 'expense'
        - description: A brief description of the transaction
        
        Optional fields:
        - category: The transaction category (e.g., 'food', 'transportation')
        - transaction_date: Date in YYYY-MM-DD format (default to today if not specified)
        - merchant: Name of the merchant/retailer
        
        Example input (image of receipt):
        Receipt showing $45.67 purchase at Walmart on May 15, 2025
        
        Example output:
        {
            "amount": 45.67,
            "transaction_type": "expense",
            "description": "Groceries at Walmart",
            "category": "groceries",
            "merchant": "Walmart",
            "transaction_date": "2025-05-15"
        }
        
        Please analyze the image and return the details in JSON format.
        """
        
        # Get current date for default value
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Send image and prompt to Gemini
        response = model.generate_content([
            prompt,
            {
                'mime_type': 'image/jpeg',  # Gemini supports various image formats
                'data': image_bytes
            }
        ])
        
        # Extract and clean response
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[response_text.find('{'):response_text.rfind('}')+1]
        
        # Parse JSON response
        transaction_data = json.loads(response_text)
        
        # Add default transaction date if not present
        if 'transaction_date' not in transaction_data:
            transaction_data['transaction_date'] = current_date
            
        # Validate required fields
        required_fields = ['amount', 'transaction_type', 'description']
        for field in required_fields:
            if field not in transaction_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Convert amount to float if needed
        if isinstance(transaction_data['amount'], str):
            transaction_data['amount'] = float(transaction_data['amount'].replace('$', '').replace(',', ''))
        
        # Validate transaction type
        if transaction_data['transaction_type'] not in ['income', 'expense']:
            raise ValueError("transaction_type must be either 'income' or 'expense'")
        
        return transaction_data
        
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from Gemini")
    except Exception as e:
        raise Exception(f"Error processing image with Gemini: {str(e)}")

# A function to test and process audio
def test_audio_processing():
    load_dotenv("secrets.env")
    try:
        # Initialize Gemini
        gemini_model = init_gemini(os.getenv('GEMINI_API_KEY'))
        
        # Test audio processing
        audio_file = open('test.mp3', 'rb')
        transaction_data = process_audio_transaction(audio_file, gemini_model)
        
        # Print the extracted transaction data
        print(transaction_data)
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")

if __name__ == '__main__':
    test_audio_processing()
    # genai.configure(api_key="AIzaSyAqMexiYlJh7pNl5rgSTWUiNUGsVKIbqkQ")
    # models = genai.list_models()
    # for model in models:
    #     print(model.name)
    