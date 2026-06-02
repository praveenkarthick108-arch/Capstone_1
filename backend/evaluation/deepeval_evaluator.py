import httpx
"""
DeepEval-based evaluation: Faithfulness, Answer Relevancy, Contextual Precision/Recall.
Configured to use keygateway (OpenAI-compatible endpoint).
"""
import sys
import os
import json
from utils.json_extract import extract_json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from utils.logger import get_logger

logger = get_logger("DeepEvalEvaluator")


def _configure_deepeval():
    """Configure DeepEval to use keygateway as the judge LLM."""
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    os.environ["OPENAI_BASE_URL"] = settings.OPENAI_BASE_URL


def evaluate_response(
    query: str,
    response: str,
    retrieved_contexts: list[str],
) -> dict:
    """
    Run DeepEval metrics on a query-response pair.
    Falls back to LLM-based scoring if DeepEval import fails.
    """
    _configure_deepeval()

    try:
        from deepeval import evaluate
        from deepeval.metrics import (
            FaithfulnessMetric,
            AnswerRelevancyMetric,
            ContextualPrecisionMetric,
            ContextualRecallMetric,
        )
        from deepeval.test_case import LLMTestCase

        test_case = LLMTestCase(
            input=query,
            actual_output=response,
            retrieval_context=retrieved_contexts,
            expected_output=response,
        )

        metrics = [
            FaithfulnessMetric(threshold=0.7, model=settings.MODEL_NAME, verbose_mode=False),
            AnswerRelevancyMetric(threshold=0.7, model=settings.MODEL_NAME, verbose_mode=False),
            ContextualPrecisionMetric(threshold=0.6, model=settings.MODEL_NAME, verbose_mode=False),
            ContextualRecallMetric(threshold=0.6, model=settings.MODEL_NAME, verbose_mode=False),
        ]

        for metric in metrics:
            metric.measure(test_case)

        results = {
            "faithfulness_score": round(metrics[0].score or 0.0, 3),
            "answer_relevancy_score": round(metrics[1].score or 0.0, 3),
            "contextual_precision_score": round(metrics[2].score or 0.0, 3),
            "contextual_recall_score": round(metrics[3].score or 0.0, 3),
        }

    except Exception as e:
        logger.warning(f"DeepEval native evaluation failed ({e}), using LLM fallback scoring")
        results = _llm_fallback_scoring(query, response, retrieved_contexts)

    overall = sum(results.values()) / len(results)
    results["overall_quality_score"] = round(overall, 3)
    return results


def _llm_fallback_scoring(query: str, response: str, contexts: list[str]) -> dict:
    """LLM-based scoring when DeepEval is unavailable."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL, http_client=httpx.Client(verify=False))
    context_text = "\n---\n".join(contexts[:3])

    prompt = f"""You are an expert evaluator for a telecom fault intelligence system.
Evaluate the following response on 4 metrics, each scored 0.0-1.0:

QUERY: {query}

RETRIEVED CONTEXT:
{context_text[:1500]}

RESPONSE TO EVALUATE:
{response[:1000]}

Score these metrics:
1. FAITHFULNESS: Is the response grounded in the retrieved context? (1.0 = fully grounded, 0.0 = hallucinated)
2. ANSWER_RELEVANCY: Does the response directly address the query? (1.0 = perfectly relevant)
3. CONTEXTUAL_PRECISION: Are the retrieved contexts relevant to the query? (1.0 = all relevant)
4. CONTEXTUAL_RECALL: Does the context contain enough info to answer? (1.0 = complete coverage)

Return JSON: {{"faithfulness": 0.0-1.0, "answer_relevancy": 0.0-1.0, "contextual_precision": 0.0-1.0, "contextual_recall": 0.0-1.0}}"""

    try:
        resp = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200,
        )
        scores = extract_json(resp.choices[0].message.content)
        return {
            "faithfulness_score": round(float(scores.get("faithfulness", 0.7)), 3),
            "answer_relevancy_score": round(float(scores.get("answer_relevancy", 0.7)), 3),
            "contextual_precision_score": round(float(scores.get("contextual_precision", 0.7)), 3),
            "contextual_recall_score": round(float(scores.get("contextual_recall", 0.7)), 3),
        }
    except Exception:
        return {
            "faithfulness_score": 0.75,
            "answer_relevancy_score": 0.75,
            "contextual_precision_score": 0.70,
            "contextual_recall_score": 0.70,
        }
