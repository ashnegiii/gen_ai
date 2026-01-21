"""
Get the FAQs and run the semantic evaluation for all questions up to the specified limit
"""
import bert_score
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv

from evaluation.db_faqs import fetch_faqs
from evaluation.candidate_client import get_candidate_answer

load_dotenv()

MODEL_TYPE = os.getenv("MODEL_TYPE", "bert-base-uncased")
MODEL_LANG = os.getenv("MODEL_LANG", "en")
RESCALE_WITH_BASELINE = os.getenv("RESCALE_WITH_BASELINE", False)


def run_evaluation(document_id: int = None, base_url: str = "http://localhost:5001", limit: int = 20):
    """
    Get FAQ question and answers for the given document ID.
    Prompt the model with the question to get an answer (candidate).
    Print BERTScore per question and overall

    :param document_id: The ID of the document that the FAQ should be taken from
    :type document_id: int
    :param base_url: The API that is used to prompt our model
    :type base_url: str
    :param limit: The number of FAQs that should be retrieved and evaluated
    :type limit: int
    """
    if document_id is not None:
        print(f"Fetching {limit} rows from document {document_id}...")
    else:
        print(f"Fetching {limit} rows for all available documents...")

    rows = fetch_faqs(document_id=document_id, limit=limit)

    candidates = []
    references = []

    print(f"Getting candidates for {len(rows)} rows...")
    for r in rows:
        q = r["question"]
        ref = r["reference_answer"]
        if document_id is not None:
            print(f"Getting candidate for FAQ #{r['faq_id']}...")
            cand = get_candidate_answer(
                base_url=base_url, question=q, document_id=document_id)
        else:
            print(
                f"Getting candidate for FAQ #{r['faq_id']} from document {r['document_id']}...")
            cand = get_candidate_answer(
                base_url=base_url, question=q, document_id=r["document_id"])

        candidates.append(cand)
        references.append(ref)

    print(f"Calculating BERTScores...")
    if MODEL_TYPE == "roberta-large":
        print(f"The following message can be ignored. This is expected:")
        print(f"-------------------------------------------------------")
    (P, R, F) = bert_score.score(
        cands=candidates,
        refs=references,
        model_type=MODEL_TYPE,
        lang=MODEL_LANG,
        rescale_with_baseline=RESCALE_WITH_BASELINE,
    )
    if MODEL_TYPE == "roberta-large":
        print(f"-------------------------------------------------------")

    now = datetime.now(ZoneInfo("Europe/Vienna"))
    results_dir = Path(__file__).resolve().parent / "results"
    out_path = results_dir / \
        f"bertscore_results_{now.strftime('%Y-%m-%d_%H%M%S')}.json"

    meta = {
        "base_url": base_url,
        "model_type": MODEL_TYPE,
        "lang": MODEL_LANG,
        "rescale_with_baseline": RESCALE_WITH_BASELINE,
        "n_samples": len(candidates),
        "created_at": now.isoformat(),
    }

    write_results_json(out_path, meta, rows, candidates, P, R, F)


def write_results_json(
    out_path: Path,
    meta: dict,
    rows: list[dict],
    candidates: list[str],
    P,
    R,
    F,
):
    samples = []
    for i, r in enumerate(rows):
        samples.append({
            "faq_id": r.get("faq_id"),
            "document_id": r.get("document_id"),
            "question": r["question"],
            "reference_answer": r["reference_answer"],
            "candidate_answer": candidates[i],
            "bertscore": {
                "precision": float(P[i].item()),
                "recall": float(R[i].item()),
                "f1": float(F[i].item()),
            }
        })

    result = {
        "meta": meta,
        "samples": samples,
        "summary": {
            "avg_precision": float(P.mean().item()),
            "avg_recall": float(R.mean().item()),
            "avg_f1": float(F.mean().item()),
        }
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(
        result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[EVALUATION] Wrote results:\n{out_path}")


if __name__ == "__main__":
    run_evaluation(os.getenv("DOCUMENT_ID", None), os.getenv(
        "BACKEND_URL", "http://localhost:5001"), os.getenv("FETCH_LIMIT", 20))
