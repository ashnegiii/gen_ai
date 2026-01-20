# Generative AI-powered project: Customer Support Chatbot 

## Setup Guide

The Backend uses **Python + Flask**. All dependencies are listed and managed in `requirements.txt`. The installation and setup is described below.

The Frontend uses **React**. All dependencies are listed and managed in `package.json`. The installation and setup is described below aswell.

## 1. Prerequisites

-   `Python 3.9+ or higher installed`
-   `pip (Python package installer)`
-   `venv`
-   `Docker` (for database setup)
-   `Node.js`
-   `npm`

Check:
```bash
python --version
pip --version
docker --version
node --version
npm --version
```

**Hint: Depending on your Python installation use either `python` or `python3` in the following commands**

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

## 4.1. Setup LLM
(If you have llama3 running locally already, you can skip this step)

Follow the instructions at ollama to install Ollama, if you haven't got Ollama installed already (https://ollama.com).

Pull the llama3 model:
```bash
ollama pull llama3
```

After installing, call
```bash
ollama list
```
to check if llama3 is available. You should see `llama3` in the list of models.

Then either call
```bash
ollama serve
```
or start the **Ollama Desktop App**.

To check if it's running, open your browser and navigate to `http://localhost:11434`. You should see the text `Ollama is running`.

## 4.2. Setup Database
The database is setup using Docker. From the project root directory, run:
```bash
# start from the project root directory
cd backend
docker-compose up -d
```

To check if the database container is running, execute:
```bash
docker ps
```
You should see a container named `postgres_genai` with the status `Up` in the list of running containers.

## 5. Run the Backend Application
Make sure the environment variable `LLAMA_MODEL` is set to `llama3` in the `.env` file. Start the application by navigating to the backend/src directory and then running app.py:
```bash
# start from the project root directory
cd backend/src
python app.py
```
## 6. Run the Frontend Application
In a separate terminal, navigate to the frontend directory and start the React application:
```bash
# start from the project root directory
cd frontend
npm install
npm run dev
```

The app is now running. Open your browser and navigate to [`http://localhost:3000`](http://localhost:3000) to start using the app.

## 7. Environment Variables

The `.env.example` file documents the required environment variables. Changes to the config can be made here.

## 8. Ideal User Flow

1. Open your browser and navigate to [`http://localhost:3000`](http://localhost:3000).
2. Upload a FAQ document - any **CSV** file with format `(question,answer)`. *Hint: Use our sample documents: `faq_example_dataset.csv` and `faq_example_dataset_2.csv`*
3. Go to "Chat" menu.
4. If multiple FAQ documents have been uploaded select the preferred document.
5. Ask any question - for best results it should relate to the questions in the uploaded FAQ.

## 9. Query Flow Pipeline:

1. User inputs query via frontend
2. Frontend sends query to POST /api/query
3. Query Rewriting:
    - Receive user query
    - Use a language model to rewrite the query for better context and clarity (Fix spelling, add context from user history, etc.)
    - Return optimized query
4. Retrieval:
    - Receive optimized query
    - Generate embedding for the query using the same embedding model used during indexing
    - Search the vector database for relevant chunks (answers) based on similarity to the query embedding
    - Rank results by similarity score
    - Return top-K relevant chunks
5. Response Generation:
    - Receive user query and relevant chunks
    - Construct a prompt combining the user query and the retrieved chunks
    - Use a language model to generate a response based on the constructed prompt
    - Return generated response to frontend
    
## Remarks

The contents of the .csv files containing questions and answers from interactions with customer support teams were written based on the contents of the synthetic dataset from [1]. Our smaller datasets are released under the “Community Data License Agreement – Sharing – Version 1.0” license.

## References

[1] "bitext" organization on GitHub, “customer-support-llm-chatbot-training-dataset“ GitHub Repository, GitHub, https://github.com/bitext/customer-support-llm-chatbot-training-dataset (last accessed Jan. 19, 2026). 
