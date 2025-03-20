# PT Reading Voice Analysis

A voice analysis and conversation platform supporting voice input, text interaction, and intelligent responses.

## Project Overview

PT Reading Voice Analysis is an application that combines speech recognition, natural language processing, and text-to-speech conversion technologies to analyze voice input and provide intelligent conversation capabilities. The project consists of a React frontend and a Flask backend, leveraging OpenAI API for intelligent conversation features.

## Project Structure

```
pt-reading-voice-analysis/
├── cache/                  # Cache files directory
├── client/                 # Frontend code
│   ├── public/             # Static resources
│   │   └── index.html      # Main HTML page
│   ├── src/                # Source code
│   │   ├── components/     # React components
│   │   │   ├── ChatInterface.jsx    # Chat interface component
│   │   │   ├── LanguageSelector.jsx # Language selector component
│   │   │   └── RecordButton.jsx     # Recording button component
│   │   ├── i18n/           # Internationalization resources
│   │   │   └── locales/    # Language packs
│   │   │       ├── en.json # English translations
│   │   │       └── zh.json # Chinese translations
│   │   ├── services/       # Services
│   │   │   └── api.js      # API call service
│   │   ├── styles/         # Style files
│   │   │   └── styles.css  # Main stylesheet
│   │   ├── App.js          # Main React application
│   │   └── index.js        # Entry point
│   ├── package.json        # Frontend dependencies and scripts
│   └── package-lock.json   # Lock file for dependencies
├── server/                 # Backend code
│   ├── controllers/        # API controllers
│   │   ├── assistant_controller.py   # OpenAI assistant controller
│   │   ├── audio_controller.py       # Audio processing controller
│   │   ├── chat_controller.py        # Chat functionality controller
│   │   ├── health_controller.py      # Health check endpoint
│   │   ├── speech_controller.py      # Speech processing controller
│   │   └── tts_controller.py         # Text-to-speech controller
│   ├── libs/               # Library modules
│   │   ├── data_source.py         # Data source management
│   │   ├── openai_assistant.py    # OpenAI assistant integration
│   │   └── prompt_templates.py    # Prompt templates for AI
│   ├── services/           # Backend services
│   │   └── openai_service.py      # OpenAI API service
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration settings
│   ├── routes.py           # API route definitions
│   ├── requirements.txt    # Python dependencies
│   └── .env.sample         # Sample environment variables
├── reference/              # Reference materials and scripts
│   └── run_task.py         # Helper script for tasks
├── run.sh                  # Project starter script
└── README.md               # This documentation file
```

## Prerequisites

Before running the application, make sure you have the following installed:

- Python 3.x
- Node.js and npm
- OpenAI API key

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd pt-reading-voice-analysis
   ```

2. Set up the environment:
   - Copy the sample environment file and update it with your OpenAI API key:
     ```bash
     cp server/.env.sample server/.env
     ```
   - Edit the `.env` file to add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

3. The `run.sh` script will handle the rest of the setup process automatically, including:
   - Creating a Python virtual environment
   - Installing backend dependencies
   - Installing frontend dependencies

## Running the Application

The project includes a convenient script that can start both frontend and backend components in either development or production mode.

### Development Mode (Default)

```bash
./run.sh
```

Or explicitly specify development mode:

```bash
./run.sh dev
```

In development mode:
- Backend runs with debug mode enabled
- Frontend uses Parcel's development server with hot reloading

### Production Mode

```bash
./run.sh prod
```

In production mode:
- Backend runs with debug mode disabled
- Frontend builds optimized assets and serves them with a static server

### Access the Application

Once running, you can access:
- Backend API: `http://localhost:8000`
- Frontend (development): `http://localhost:1234`
- Frontend (production): `http://localhost:3000`

## Features

- **Voice Recording**: Record voice input for analysis
- **Speech-to-Text**: Convert spoken language to text
- **Intelligent Conversation**: Chat with an AI assistant
- **Text-to-Speech**: Convert text responses to speech
- **Multilingual Support**: Toggle between English and Chinese interfaces
- **Voice Analysis**: Analyze speech patterns and characteristics

## API Endpoints

- `/api/health`: Health check endpoint
- `/api/chat`: Text-based chat interaction
- `/api/speech`: Speech processing endpoints
- `/api/audio`: Audio processing endpoints
- `/api/tts`: Text-to-speech conversion

## Troubleshooting

If you encounter any issues:

1. Ensure your OpenAI API key is correctly set in the `.env` file
2. Check that all required dependencies are installed
3. Verify that both frontend and backend are running
4. Check the terminal output for any error messages

## Stopping the Application

To stop all running components, press `Ctrl+C` in the terminal where you started the application. The script will gracefully shut down all processes.
