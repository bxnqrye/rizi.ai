# Jarvis — AI Chatbot

A personal AI chatbot built using Python, Streamlit, and Google's Gemini API.

## Features

- User registration and authentication
- AI-powered conversations using Google Gemini
- Multiple chat sessions
- Chat history within the current session
- Copy AI responses
- Dark-themed interface with red accents
- SQLite database for user accounts

## Tech Stack

- Python
- Streamlit
- Google Gemini API
- SQLite
- HTML/CSS

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/jarvis-ai-chatbot.git
cd jarvis-ai-chatbot
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure your API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

### 4. Run the application

```bash
python -m streamlit run rizi.py
```

## Security

API keys and local user databases are excluded from version control using `.gitignore`.

## Project Status

Currently under development.