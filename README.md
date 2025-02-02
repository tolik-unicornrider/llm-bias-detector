# AI Chat Assistant

A Streamlit-based chat application that allows you to interact with multiple AI models including OpenAI's GPT and Google's Gemini.

## Setup Instructions

### 1. Environment Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Fill in your API keys in the `.env` file:
   - `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - `OPENAI_API_KEY`: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

### 2. Package Management with uv

This project uses `uv` for fast Python package management. Install it first:

```bash
pip install uv
```

Install project dependencies:
```bash
uv venv
uv pip install -r requirements.txt
```

### 3. Running the Application

Start the Streamlit app:
```bash
streamlit run src/app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Features

- Chat with multiple AI models in one interface
- Switch between different AI providers (OpenAI, Google)
- Clean and intuitive user interface
- Real-time responses
- Message history tracking

## Requirements

- Python 3.8+
- OpenAI API key
- Google Gemini API key
