from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import requests # For Ollama API
from PIL import Image # For image processing
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ollama API Configuration (example, adjust as needed)
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate") # Default if not in .env
DEFAULT_THRESHOLDS = {
    "found_low": 0.8,
    "maybe_low": 0.5,
}

def parse_ollama_response(raw_text, custom_items_queried):
    app.logger.info(f"Parsing Ollama response. Custom items queried: {custom_items_queried}")
    app.logger.debug(f"Raw Ollama response to parse:\n{raw_text}")

    found_items = []
    maybe_found_items = []
    not_found_items = []
    # queried_items_echoed_by_model list is removed as the model will no longer output this section

    import re

    lines = raw_text.split('\n')
    current_category = None # Can be 'found', 'maybe_found', 'not_found'

    # Regex for headers: e.g., **Found Items:**, **Maybe Found Item:**, **Not Found Item:**
    # Removed "Specified" from this pattern
    header_pattern = re.compile(r"^\*\*(Found|Maybe Found|Not Found) Items?:\*\*|^\*\*(Maybe Found|Not Found) Item:\*\*", re.IGNORECASE)

    # Regex for items under headers: e.g., * item name (optional details)
    item_pattern = re.compile(r"^\*\s*(.*?)(?:\s*\((.*?)\))?$")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        header_match = header_pattern.match(line)
        if header_match:
            # Group 1 will be the main category, Group 2 for singular "Maybe Found Item" or "Not Found Item"
            category_name_match = header_match.group(1) or header_match.group(2)
            if category_name_match:
                current_category = category_name_match.lower().replace(" ", "_").replace("_items", "").replace("_item", "") # e.g., "maybe_found"
                app.logger.info(f"Switched to category: {current_category}")
            else:
                # This case should ideally not be reached if regex is correct
                app.logger.warning(f"Header matched but no category group captured: {line}")
                current_category = None
            continue # Move to the next line after identifying a header

        if current_category:
            item_match = item_pattern.match(line)
            if item_match:
                item_name = item_match.group(1).strip()
                details = item_match.group(2).strip() if item_match.group(2) else None
                
                item_data = {"item": item_name}
                if details:
                    item_data["details"] = details

                # Removed "specified" category handling
                if current_category == "found":
                    found_items.append(item_data)
                elif current_category == "maybe_found":
                    maybe_found_items.append(item_data)
                elif current_category == "not_found":
                    not_found_items.append(item_data)
            else:
                app.logger.debug(f"Line under '{current_category}' did not match item pattern: '{line}'")
        else:
            app.logger.debug(f"Line not processed (no current category): '{line}'")

    # Ensure all originally queried items are accounted for
    if custom_items_queried:
        all_reported_items_names = [fi['item'] for fi in found_items] + \
                                   [mfi['item'] for mfi in maybe_found_items] + \
                                   [nfi['item'] for nfi in not_found_items]
                                   # Removed queried_items_echoed_by_model from this check

        for queried_item_name in custom_items_queried:
            is_mentioned = any(queried_item_name.lower() == reported_item_name.lower() for reported_item_name in all_reported_items_names)
            if not is_mentioned:
                app.logger.info(f"Custom queried item '{queried_item_name}' not explicitly found in model's output, adding to 'not_found'.")
                # not_found_items.append({"item": queried_item_name, "details": "Queried item not explicitly categorized by model."})
    
    # The parsed response no longer includes queried_items_echoed from the model's output
    app.logger.info(f"Parsed items - Found: {len(found_items)}, Maybe: {len(maybe_found_items)}, Not Found: {len(not_found_items)}")
    return {
        "found": found_items,
        "maybe_found": maybe_found_items,
        "not_found": not_found_items
    }

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # For FR002: Return image path for preview
        return jsonify({'message': 'Image uploaded successfully', 'filepath': filepath}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

# Placeholder for FR004 - Model Selection (will be enhanced later)
@app.route('/models', methods=['GET'])
def get_models():
    # In a real scenario, you'd query Ollama for available models
    # For now, returning a static list
    # We will later integrate this with Ollama's API to list actual local models
    default_fallback_models = ['llava:latest'] # Define default fallback
    try:
        # Attempt to list local Ollama models
        ollama_list_url = os.getenv("OLLAMA_LIST_MODELS_URL", "http://localhost:11434/api/tags")
        response = requests.get(ollama_list_url, timeout=5) # Added timeout
        response.raise_for_status() # Raise an exception for HTTP errors
        models_data = response.json()
        # Extract model names, assuming 'models' is a list of dicts with a 'name' key
        model_names = [model.get('name') for model in models_data.get('models', []) if model.get('name')]
        if not model_names:
            # Ollama reachable but no models or unexpected format
            app.logger.warn("Ollama API returned no models or in an unexpected format.")
            return jsonify({'models': default_fallback_models, 'warning': 'Ollama reported no models. Using default.'}), 200
        return jsonify({'models': model_names})
    except requests.exceptions.Timeout:
        app.logger.error(f"Timeout connecting to Ollama to list models at {ollama_list_url}")
        return jsonify({'error': 'Timeout connecting to Ollama to list models. Using default.', 'models': default_fallback_models}), 504 # Gateway Timeout
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Could not connect to Ollama to list models: {e}")
        # Fallback to a default model if Ollama is not reachable or has no models
        return jsonify({'error': f'Could not connect to Ollama to list models ({e.__class__.__name__}). Using default.', 'models': default_fallback_models}), 503 # Service Unavailable

# Placeholder for FR005 & FR003 - Image Analysis & Ollama Integration
@app.route('/analyze', methods=['POST'])
def analyze_image():
    data = request.get_json()
    image_path = data.get('image_path')
    model_name = data.get('model', 'llava:latest')
    custom_prompt_items = data.get('custom_items', []) # FR011
    # Thresholds are not directly used by the new parser but kept for potential future use
    # thresholds_input = data.get('thresholds', DEFAULT_THRESHOLDS) 
    # current_thresholds = {
    #     "found_low": float(thresholds_input.get("found_low", DEFAULT_THRESHOLDS["found_low"])),
    #     "maybe_low": float(thresholds_input.get("maybe_low", DEFAULT_THRESHOLDS["maybe_low"])),
    # }

    if not image_path or not os.path.exists(image_path):
        return jsonify({'error': 'Image path is missing or invalid'}), 400

    try:
        with open(image_path, "rb") as f:
            image_data = f.read()

        prompt_text = "Analyze the provided image. "
        if custom_prompt_items:
            items_to_find_str = ", ".join(custom_prompt_items)
            prompt_text += f"You are tasked with finding *only* the following specific items in the image: {items_to_find_str}. Do not identify or list any other items. "
        else:
            prompt_text += "Analyze the image for any notable items. "
        
        # Removed instruction for "**Specified Items:**" header
        prompt_text += "Present your findings using the following exact headers and format for each category if items are found (omit category if no items):\n"
        prompt_text += "**Found Items:**\n* [item_name_1] (optional brief detail)\n* [item_name_2]\n...\n"
        prompt_text += "**Maybe Found Item:**\n* [item_name_3] (optional brief detail)\n...\n"
        prompt_text += "**Not Found Item:**\n* [item_name_4]\n...\n"
        prompt_text += "List each item on a new line, prefixed with '* '. Do not add any other comments or explanations outside of the optional brief detail in parentheses for an item. If no items are found for a category, omit the header for that category entirely."


        import base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')

        payload = {
            "model": model_name,
            "prompt": prompt_text,
            "images": [encoded_image],
            "stream": False
        }

        app.logger.info(f"Sending request to Ollama: {OLLAMA_API_URL} with model {model_name}")
        app.logger.debug(f"Prompt sent to Ollama:\n{prompt_text}")

        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        analysis_result = response.json()

        app.logger.info(f"Ollama raw response JSON: {analysis_result}") # Log the full JSON
        raw_model_output = analysis_result.get('response', 'No response content from model.')

        parsed_data = parse_ollama_response(raw_model_output, custom_prompt_items) 
        
        # Populate queried_items_echoed directly from the user's input custom_prompt_items
        queried_items_for_response = [{"item": item_name} for item_name in custom_prompt_items]

        categorized_results = {
            "queried_items_echoed": queried_items_for_response,
            "found": parsed_data["found"],
            "maybe_found": parsed_data["maybe_found"],
            "not_found": parsed_data["not_found"],
            "raw_output": raw_model_output
        }

        return jsonify(categorized_results), 200

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Ollama API request failed: {e}")
        return jsonify({'error': f'Failed to connect to Ollama or process image: {str(e)}'}), 500
    except FileNotFoundError:
        return jsonify({'error': 'Image file not found after upload.'}), 404
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
