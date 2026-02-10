from openai import OpenAI
import re
from decouple import config
import logging

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an expert Prompt Engineer and Linguistic Analyst acting as a strict, critical Auditor. Your task is to evaluate the user's input based on grammar, clarity, intent, and structural effectiveness with zero tolerance for ambiguity or errors.

Adhere to the following strict guidelines for every response:

1. Language Detection: Automatically detect the language of the user's input. You must provide your entire response in that exact same language.
2. Tone: Be harsh, direct, and efficient. Focus solely on the flaws and the fix.
3. Output Structure: Your response must start immediately with the score and advice in the exact format below. Do not use labels like 'Score:' or write any introductory text.

    [X]/10 (short, direct comment about the errors in the prompt)

4. Optimization: Immediately after the advice, on a new line write:

    Refined: "[optimized prompt, within 500 characters]"

5. Mandatory rules:
   - The first line must always be in the format [X]/10 (text).
   - The second line must always start with "Refined: \"".
   - No additional explanations, headings, or lists outside this format.
   - If you cannot evaluate, return [5.0]/10 (Could not parse the score.)
   - If you cannot optimize, return Refined: "[repeat the input prompt, unchanged]"."""


def get_client() -> OpenAI:
    api_key = config("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError("PERPLEXITY_API_KEY is not set")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.perplexity.ai",
    )


def parse_score_and_refined(response_text: str) -> tuple[float, str, str]:
    logger.debug("Perplexity response: %s", response_text)

    lines = response_text.strip().splitlines()
    first_line = lines[0] if lines else ""

    score_match = re.search(
        r"\[(\d+(?:\.\d+)?)\]/10\s*\((.*?)\)", first_line, re.DOTALL
    )
    if not score_match:
        return 5.0, "Не вдалося розібрати оцінку.", response_text[:500]

    score_str, advice = score_match.groups()
    try:
        score = max(1.0, min(10.0, float(score_str)))
    except ValueError:
        return 5.0, "Не вдалося розібрати оцінку.", response_text[:500]
    refined_text = ""
    for line in lines[1:]:
        line = line.strip()
        m = re.search(
            r"^(?:Refined|Optimized|Оптимізований|Refined prompt|Optimized prompt):\s*\"?([^\"]+)",
            line,
            re.IGNORECASE,
        )
        if m:
            refined_text = m.group(1).strip()
            break

    if not refined_text:
        refined_text = "\n".join(lines[1:]).strip()

    return score, advice.strip(), refined_text[:500]


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
        logger.exception("Perplexity evaluation failed: %s", e)
        return 5.0, "Помилка при оцінці промпта.", prompt_text[:500]
