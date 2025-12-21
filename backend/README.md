# Flask Backend - Setup Guide

This Python uses **Python + Flask**.
All dependencies are listed and managed in `requirements.txt`.

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

## 3. Install dependencies (first setup)

```bash
pip install -r requirements.txt
```

## 4. Run the Flask application

```bash
python src/app.py
```

## 5. Adding new dependencies

Whenever you add a new dependency, make sure to update `requirements.txt`:

If you install a new package, run:

```
pip install <package-name>
```

Then, update `requirements.txt` automatically with:

```bash
pip freeze > requirements.txt
```

## 6. Environment Variables

I have added a `.env.example` file to document the required environment variables.
Please create a local `.env` file in the backend/ directory based on this example and populate it with the appropriate values.
Make sure to inform the team when new environment variables are added (e.g. database configuration).

## 7. Architecture Overview

### 1. Define Database schema (Kevin):

1. Define database schema and indexes for storing documents, embeddings and metadata
2. Set up database connection and ORM models

### 2. Indexing (Kevin):

1. User uploads file via frontend drag-drop
2. Frontend sends file to POST /api/upload
3. Extract text from file (PDF, CSV, DOCX, etc.) (file format and data structure need to be discussed)
4. Preprocess text (cleaning, normalization, remove headers/footers, tables handling etc.) (to be discussed)
5. Chunk text based on a predefined strategy (e.g., size, sentences, etc.)
6. Generate embeddings for each chunk using an embedding model
7. Store embeddings and associated metadata in a vector database (postgres with pgvector?):
8. Return success response to frontend

### 3. Query Flow Pipeline (Kevin -> Paula -> Moritz):

1. User inputs query via frontend
2. Frontend sends query to POST /api/query
3. Query Rewriting (Kevin):
    - Receive user query
    - Use a language model to rewrite the query for better context and clarity (Fix spelling, add context from user history, etc.)
    - Return opitimized query
4. Retrieval (Paula):
    - Receive optimized query
    - Generate embedding for the query using the same embedding model used during indexing
    - Search the vector database for relevant chunks based on similarity to the query embedding
    - Rank by similarity score
    - Top-K relevant chunks based on a predefined strategy (e.g., top-k, threshold score, etc.)
    - Return top-k relevant chunks with metadata
5. Response Generation (Moritz):
    - Receive user query and relevant chunks
    - Construct a prompt combining the user query and the retrieved chunks
    - Use a language model to generate a response based on the constructed prompt
    - Return generated response to frontend

If you have any questions or run into issues, feel free to reach out to me.
