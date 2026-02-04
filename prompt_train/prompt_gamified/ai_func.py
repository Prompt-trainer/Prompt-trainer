from openai import OpenAI
import os
import re
from decouple import config
import logging
logger = logging.getLogger(__name__)



SYSTEM_PROMPT = (
    "You are an expert Prompt Engineer and Linguistic Analyst acting as a strict, critical Auditor. "
    "Your task is to evaluate the user's input based on grammar, clarity, intent, and structural effectiveness "
    "with zero tolerance for ambiguity or errors.\n\n"
    "Adhere to the following strict guidelines for every response:\n\n"
    "1. Language Detection: Automatically detect the language of the user's input. "
    "You must provide your entire response in that exact same language.\n"
    "2. Tone: Be harsh, direct, and efficient. Focus solely on the flaws and the fix.\n"
    "3. Output Structure: Your response must start immediately with the score and advice "
    "in the exact format below. Do not use labels like 'Score:' or write any introductory text.\n\n"
    "    [X]/10 ([Direct, concise advice on how to fix the grammar, clarity, or logic])\n\n"
    "4. Optimization: Immediately after the advice, provide a single, refined version of the prompt "
    "that solves the identified problems."
)


def get_client() -> OpenAI:
    api_key = config("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError("PERPLEXITY_API_KEY is not set")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.perplexity.ai",
    )


def parse_score_and_refined(response_text: str) -> tuple[float, str, str]:
    match = re.search(r"\[(\d+(?:\.\d+)?)\]/10\s*\((.*?)\)", response_text, re.DOTALL)
    if not match:
        return 5.0, "Не вдалося розібрати оцінку.", response_text[:500]

    score_str, advice = match.groups()
    score = max(1.0, min(10.0, float(score_str)))

    refined_match = re.search(r"Refined:\s*\"([^\"]+)\"", response_text)
    if refined_match:
        refined = refined_match.group(1)
    else:
        lines = response_text.splitlines()
        refined = "\n".join(lines[1:]).strip()[:500]

    return score, advice.strip(), refined.strip()


def evaluate_prompt_quality(prompt_text: str) -> tuple[float, str, str]:
    try:
        client = get_client()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text},
        ]
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=messages,
            temperature=0.5,
            max_tokens=500,
        )
        ai_text = response.choices[0].message.content
        rate, improvement_hint, refined_prompt = parse_score_and_refined(ai_text)

        improvement_hint = improvement_hint[:164]
        refined_prompt = refined_prompt[:500]

        return rate, improvement_hint, refined_prompt
    except Exception as e:
        logger.exception("Perplexity evaluation failed")
        return 5.0, str(e), prompt_text[:500]