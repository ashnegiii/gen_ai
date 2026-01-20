# Setup Guide

The Backend uses **Python + Flask**. All dependencies are listed and managed in `requirements.txt`. The installation and setup is described below.

The Frontend uses **React**. All dependencies are listed and managed in `package.json`. The installation and setup is described below aswell.

## 1. Prerequisites

-   `Python 3.9+ or higher installed`
-   `pip (Python package installer)`
-   `venv`

Check:
```bash
python --version
pip --version
```
## 2. Create and activate virtual environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

## 3. Install dependencies
(Only needed for the first setup):
```bash
pip install -r requirements.txt
```

## 4. Setup LLM
(If you have llama3 running locally already, you can skip this step)

Follow the instructions at ollama to install Ollama, if you haven't got Ollama installed already (https://ollama.com/download/windows).

Install llama3:
```bash
ollama pull llama3
```

After installing, call
```bash
ollama list
```
to verify that llama3 is installed. You should see `llama3` in the list of models. Run `llama3` by calling
```bash
ollama run llama3
```

## 4. Run theFlask application
Make sure the environment variable `LLAMA_MODEL` is set to `llama3` in the `.env` file. Start the application by navigating to the backend/src directory and then runnging app.py:
```bash
cd backend/src
python src/app.py
```
## 5. Run Frontend application
In a separate terminal, navigate to the frontend directory and start the React application:
```bash
cd frontend # start from the project root directory
npm install
npm run dev
```

## 6. Environment Variables

The `.env.example` file documents the required environment variables. Changes to the config can be made here.

## 7. Query Flow Pipeline:

1. User inputs query via frontend
2. Frontend sends query to POST /api/query
3. Query Rewriting:
    - Receive user query
    - Use a language model to rewrite the query for better context and clarity (Fix spelling, add context from user history, etc.)
    - Return opitimized query
4. Retrieval:
    - Receive optimized query
    - Generate embedding for the query using the same embedding model used during indexing
    - Search the vector database for relevant chunks based on similarity to the query embedding
    - Rank by similarity score
    - Top-K relevant chunks based on a predefined strategy (e.g., top-k, threshold score, etc.)
    - Return top-k relevant chunks with metadata
5. Response Generation:
    - Receive user query and relevant chunks
    - Construct a prompt combining the user query and the retrieved chunks
    - Use a language model to generate a response based on the constructed prompt
    - Return generated response to frontend
