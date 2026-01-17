"""
Fetch and return FAQs from the database
"""
import bert_score

from src.evaluation.db_faqs import fetch_faqs
from src.evaluation.candidate_client import get_candidate_answer


def run_evaluation(document_id: int = 1, base_url: str = "http://localhost:5000", limit: int = 3):
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
    rows = fetch_faqs(document_id=document_id, limit=limit)

    cands = []
    refs = []

    for r in rows:
        q = r["question"]
        ref = r["reference_answer"]
        cand = get_candidate_answer(
            base_url=base_url, question=q, document_id=str(document_id))

        cands.append(cand)
        refs.append(ref)

    (P, R, F) = bert_score.score(
        cands,
        refs,
        model_type="roberta-large",
        lang="en",
        rescale_with_baseline=True,
    )

    # Per-sample results
    for i, r in enumerate(rows):
        print(f"\nFAQ {r['faq_id']}")
        print("Q: ", r["question"])
        print("Ref:", r["reference_answer"])
        print("Cand:", cands[i])
        print(
            f"BERTScore: P={P[i].item():.4f} R={R[i].item():.4f} F={F[i].item():.4f}")

    # Aggregate
    print("\n--- Aggregate ---")
    print(f"Avg P: {P.mean().item():.4f}")
    print(f"Avg R: {R.mean().item():.4f}")
    print(f"Avg F: {F.mean().item():.4f}")


if __name__ == "__main__":
    run_evaluation()
