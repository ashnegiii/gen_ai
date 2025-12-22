from flask import Flask, request, jsonify

from services.generation_service import GenerationService
from services.indexing_service import IndexingService
from services.retrieval_service import RetrievalService


app = Flask(__name__)

indexing_service = IndexingService()

retrieval_service = RetrievalService()

generation_service = GenerationService()


@app.route("/api/upload", methods=["POST"])
def upload():
    """
    Upload and index documents using (optionally) chunking strategies.
    """
    try:
        data = request.get_json()
        documents = data.get("documents", [])
        
        result = indexing_service.index_documents(documents)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/api/query', methods=["POST"])
def chat():
    """
    Main RAG endpoint.
    Call the pipeline here defined in pipeline.py

    Pipeline:
    1. Kevin: Query rewriting/optimization
    2. Paula: Retrieve relevant documents
    3. Moritz: Prompt engineering and LLM generation
    """
    pass


if __name__ == "__main__":
    app.run(debug=True)
