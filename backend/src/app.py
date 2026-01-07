import csv
import io
import time

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from pipeline import RAGPipeline

from services.generation_service import GenerationService
from services.indexing_service import IndexingService
from services.query_rewriting_service import QueryRewritingService
from services.retrieval_service import RetrievalService

app = Flask(__name__)
CORS(app)
indexing_service = IndexingService()

query_rewriting_service = QueryRewritingService()

retrieval_service = RetrievalService()

generation_service = GenerationService()


@app.route("/api/upload", methods=["POST"])
def upload():
    """
    Upload and index documents using (optionally) chunking strategies.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file found"}), 400
        
        # get file from request
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        # read file content
        file_content = file.read()
        file_size = len(file_content)
        filename = file.filename

        stream = io.StringIO(file_content.decode("UTF-8"), newline=None)
        csv_input = csv.DictReader(stream)
        
        faq_entries = []
        for row in csv_input:
            q = row.get("question")
            a = row.get("answer")
            if q and a:
                faq_entries.append({
                    "question": q,
                    "answer": a
                })

        if not faq_entries:
            return jsonify({"status": "error", "message": "CSV is empty or incorrectly formatted"}), 400

        # call indexing service
        result = indexing_service.index_documents(
            filename=filename,
            file_size=file_size,
            faq_entries=faq_entries
        )

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

    data = request.get_json()
    # the user's original question/query
    query = data.get("query")
    # the id of the document to restrict the retrieval to
    document_id = data.get("documentId")
    # chat history for conversational context (last 5 messages)
    chat_history = data.get("chatHistory", [])

    # 1. Kevin: Query rewriting/optimization (with chat history for context resolution)
    rewritten = query_rewriting_service.rewrite_query(query, chat_history=chat_history)
    optimized_query = rewritten["cleaned_query"]

    # 2. Paula: Retrieve relevant documents ONLY from the selected document_id
    # context = retrieval_service.retrieve(query=optimized_query, document_id=document_id)

    # 3. Moritz: Prompt engineering and LLM generation
    # For streaming, you would return a Response(generation_service.stream_answer(query, context)) or sum shit like that    
    # TODO: For now, return a dummy response for testing query rewriting
    return Response(
        f"[DEBUG] Query rewriting test:\nOriginal: {query}\nOptimized: {optimized_query}\nIs Contextual: {rewritten['is_contextual']}",
        mimetype="text/plain"
    )


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """
    List all indexed documents.
    Returns documents with id, name, uploadedAt, and size.
    """
    try:
        documents = indexing_service.get_all_documents()
        return jsonify({"documents": documents}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/documents", methods=["DELETE"])
def delete_document():
    """
    Delete a document by ID.
    Expects JSON body with 'id' field.
    """
    try:
        data = request.get_json()
        doc_id = data.get("id")

        if not doc_id:
            return jsonify({
                "status": "error",
                "message": "Document id is required"
            }), 400

        result = indexing_service.delete_document(doc_id)
        
        if result["status"] == "error":
            return jsonify(result), 404
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


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
