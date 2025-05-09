# Image Item Recognizer

This project is a web application that allows users to upload images and uses an Ollama model to recognize items within those images.

## Features

*   **Image Upload:** Users can upload images (PNG, JPG, GIF) for analysis.
*   **Ollama Integration:** Utilizes a local Ollama instance for image recognition.
*   **Model Selection:** Users can select from available Ollama models.
*   **Custom Item Search:** Users can specify a list of items to look for in the image.
*   **Categorized Results:** Displays results categorized as "Found," "Maybe Found," and "Not Found."
*   **Adjustable Thresholds:** Allows adjustment of confidence thresholds for categorization (frontend UI).

## Project Structure

```
├── app.py                # Main Flask application
├── requirements.txt      # Python dependencies
├── static/               # Static assets (CSS, JavaScript, uploaded images)
│   ├── css/style.css
│   ├── js/main.js
│   └── uploads/          # Directory for uploaded images
├── templates/
│   └── index.html        # Main HTML template
└── README.md             # This file
```

## Setup and Run

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <your-repository-url>
    cd Tech_e_challenge
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Ollama:**
    Ensure you have Ollama running and accessible. By default, the application tries to connect to `http://localhost:11434`. You might need to pull a model like `llava`:
    ```bash
    ollama pull llava
    ```
    You can configure the Ollama API URL via an `.env` file (see `OLLAMA_API_URL` in `app.py`).

5.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    The application will be available at `http://127.0.0.1:5000/`.

## Key Files

*   `app.py`: Contains the Flask backend logic, including image uploading, Ollama API interaction, and response parsing.
*   `static/js/main.js`: Handles frontend interactions, API calls to the Flask backend, and dynamic updates to the page.
*   `templates/index.html`: The main HTML structure of the web application.
*   `static/css/style.css`: Styles for the web application.

## Environment Variables

The application can use a `.env` file for configuration. A key variable is:

*   `OLLAMA_API_URL`: The URL for the Ollama API (e.g., `http://localhost:11434/api/generate`).
*   `OLLAMA_LIST_MODELS_URL`: The URL to list Ollama models (e.g., `http://localhost:11434/api/tags`).

Create a `.env` file in the root directory if you need to override the defaults:
```
OLLAMA_API_URL=http://your_ollama_host:11434/api/generate
OLLAMA_LIST_MODELS_URL=http://your_ollama_host:11434/api/tags
```
