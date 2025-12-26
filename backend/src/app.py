import time

from flask import Flask, Response, request, jsonify

from services.generation_service import GenerationService
from services.indexing_service import IndexingService
from services.retrieval_service import RetrievalService
from flask_cors import CORS
from pipeline import RAGPipeline


app = Flask(__name__)
CORS(app)
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


#@app.route('/api/query', methods=["POST"])
def chat():
    """
    Main RAG endpoint.
    Call the pipeline here defined in pipeline.py

    Pipeline:
    1. Kevin: Query rewriting/optimization
    2. Paula: Retrieve relevant documents
    3. Moritz: Prompt engineering and LLM generation
    """


# TODO kevin: can you implement document listing?
@app.route("/api/documents", methods=["GET"])
def list_documents():
    """
    List all indexed documents.
    (Stub version – no DB yet)
    """
    return jsonify({"documents": []}), 200


# TODO kevin: can you implement document deletion by id?
@app.route("/api/documents", methods=["DELETE"])
def delete_document():
    """
    Delete a document by ID.
    (Stub version – no DB yet)
    """

    data = request.get_json()
    doc_id = data.get("id")

    if not doc_id:
        return jsonify({
            "status": "error",
            "message": "Document id is required"
        }), 400

    # TODO: delete from DB / filesystem / index
    print(f"Deleting document with id: {doc_id}")

    return jsonify({
        "status": "success",
        "id": doc_id
    }), 200


# NOTE: only for testing streaming responses (delete when llm streaming is implemented)
@app.route("/api/chat", methods=["POST"])
def chat_test():
    """
    Streaming test endpoint.
    Sends a fake assistant response in chunks.
    """

    data = request.get_json()
    query = data.get("query", "")

    rag_pipeline = RAGPipeline()
    rag_pipeline.query(query)

    def generate():
        # Example streamed answer
        answer = (
            f"""Your query was: {query}. \nI'm sorry you're having trouble receiving the password reset email. This issue is usually caused by one of the following reasons:
First, please double-check that the email address you entered is the one associated with your account. Even a small typo can prevent the email from being delivered.
If the address is correct, make sure that emails from our domain are not being blocked by your email provider. Adding our support address to your contacts or allowlist can help.
In some cases, corporate or university email systems automatically filter automated emails. If possible, try using a personal email address instead.
You should also wait a few minutes and avoid requesting multiple reset emails in a short period, as this can temporarily block further messages.
If you still don't receive the email after trying these steps, please contact our support team and we can manually assist you with resetting your password.""")

        for token in answer.split(" "):
            yield token + " "
            time.sleep(0.01)

    return Response(
        generate(),
        mimetype="text/plain"
    )


if __name__ == "__main__":
    app.run(debug=True)
