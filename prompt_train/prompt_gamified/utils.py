import random
from django.db import transaction
from .models import Prompt
from .ai_func import evaluate_prompt_quality


def get_random_high_rated_prompt(min_rate=7) -> Prompt | None:
    high_rated_prompts = Prompt.objects.filter(rate__gte=min_rate)

    if not high_rated_prompts.exists():
        return None

    return random.choice(high_rated_prompts)


def get_random_low_rated_prompt(max_rate=4) -> Prompt | None:
    low_rated_prompts = Prompt.objects.filter(rate__lte=max_rate)

    if not low_rated_prompts.exists():
        return None

    return random.choice(low_rated_prompts)


def get_difference_between_rates(user) -> tuple[int, int]:
    rank = getattr(user, "rank", None) or "B"

    difference_by_rank = {
        "B": (8, 2),
        "S": (8, 3),
        "G": (7, 4),
        "R": (7, 5),
        "D": (6, 5),
    }

    return difference_by_rank.get(rank, (8, 2))


def validate_user_prompt(user_prompt_text: str) -> tuple[bool, str | None]:
    if not user_prompt_text:
        return False, "Будь ласка, введіть промпт."

    if len(user_prompt_text) > 500:
        return False, "Промпт має бути не більше 500 символів."

    return True, None


def calculate_challenge_result(
    user_rate: float, challenge_rate: int
) -> tuple[str, str]:
    if user_rate > challenge_rate:
        return "win", "Перемога! Ваш промпт кращий!"
    elif user_rate == challenge_rate:
        return "draw", "Нічия! Ваш промпт такий же хороший!"
    else:
        return "loss", "Програш. Спробуйте ще раз!"


def award_user_points(user, result: str) -> None:
    if result == "win":
        user.exp += 2
        user.points += 30
    elif result == "draw":
        user.exp += 1
        user.points += 10

    with transaction.atomic():
        user.save(update_fields=["exp", "points"])


def create_user_prompt(user_prompt_text: str, user) -> tuple[float, str, str]:

    user_rate, improvement_hint, refined_prompt = evaluate_prompt_quality(
        user_prompt_text
    )

    Prompt.objects.create(
        prompt_text=user_prompt_text,
        improvement_hint=improvement_hint,
        rate=user_rate,
        user=user,
    )

    return user_rate, improvement_hint, refined_prompt


def handle_challenge_get(request) -> dict:
    context = {}

    challenge_prompt = get_random_high_rated_prompt()

    if not challenge_prompt:
        context["error"] = "Поки що немає промптів з оцінкою 7+. Спробуйте пізніше!"
        return context

    request.session["challenge_prompt_id"] = challenge_prompt.id
    context["challenge_prompt"] = challenge_prompt

    return context


def handle_challenge_post(request) -> dict:
    context = {}

    user_prompt_text = request.POST.get("prompt", "").strip()
    challenge_prompt_id = request.session.get("challenge_prompt_id")

    if not challenge_prompt_id:
        return None

    try:
        challenge_prompt = Prompt.objects.get(id=challenge_prompt_id)
    except Prompt.DoesNotExist:
        return None

    is_valid, error_message = validate_user_prompt(user_prompt_text)
    if not is_valid:
        context["error"] = error_message
        context["challenge_prompt"] = challenge_prompt
        return context

    user_rate, improvement_hint, refined_prompt = create_user_prompt(
        user_prompt_text, request.user
    )

    result, message = calculate_challenge_result(user_rate, challenge_prompt.rate)

    award_user_points(request.user, result)

    if "challenge_prompt_id" in request.session:
        del request.session["challenge_prompt_id"]

    context.update(
        {
            "result": result,
            "message": message,
            "user_prompt": user_prompt_text,
            "user_rate": user_rate,
            "challenge_prompt": challenge_prompt,
            "challenge_rate": challenge_prompt.rate,
            "improvement_hint": improvement_hint,
            "refined_prompt": refined_prompt,
        }
    )

    return context


def handle_prompt_trainer_post(user, user_message: str) -> tuple[dict, str | None]:
    user_message = user_message.strip()

    if not user_message:
        return {}, "Будь ласка, введіть промпт."

    if len(user_message) > 500:
        return {}, "Промпт має бути не більше 500 символів."

    rate, improvement_hint, refined_prompt = evaluate_prompt_quality(user_message)

    Prompt.objects.create(
        prompt_text=user_message,
        improvement_hint=improvement_hint,
        rate=rate,
        user=user,
    )

    updated_fields = []
    if rate > 7:
        user.exp += 1
        updated_fields.append("exp")
    if rate >= 8:
        user.points += 20
        updated_fields.append("points")

    if updated_fields:
        with transaction.atomic():
            user.save(update_fields=updated_fields)

    context = {
        "prompt_text": user_message,
        "prompt_rate": rate,
        "improvement_hint": improvement_hint,
        "refined_prompt": refined_prompt,
    }
    return context, None


def handle_guess_the_best_prompt_get(request) -> dict:
    context = {}

    min_rate, max_rate = get_difference_between_rates(request.user)
    high_rated_prompt = get_random_high_rated_prompt(min_rate=min_rate)
    low_rated_prompt = get_random_low_rated_prompt(max_rate=max_rate)

    if not high_rated_prompt or not low_rated_prompt:
        context["error"] = "Недостатньо промптів для гри. Спробуйте пізніше!"
        return context

    prompts = [high_rated_prompt, low_rated_prompt]
    random.shuffle(prompts)

    request.session["best_prompt_id"] = high_rated_prompt.id
    context["prompts"] = prompts

    return context


def handle_guess_the_best_prompt_post(request) -> dict | None:
    context = {}

    user_choice_id = request.POST.get("prompt_id")
    best_prompt_id = request.session.get("best_prompt_id")

    if not best_prompt_id or not user_choice_id:
        return None

    try:
        best_prompt = Prompt.objects.get(id=best_prompt_id)
        chosen_prompt = Prompt.objects.get(id=user_choice_id)
    except Prompt.DoesNotExist:
        return None

    is_correct = int(user_choice_id) == best_prompt_id
    result = "win" if is_correct else "loss"
    message = (
        "Правильно! Ви обрали найкращий промпт!"
        if is_correct
        else "Неправильно. Це був не кращий промпт!"
    )

    award_user_points(request.user, result)

    if "best_prompt_id" in request.session:
        del request.session["best_prompt_id"]

    worst_prompt = chosen_prompt if not is_correct else None

    context.update(
        {
            "result": result,
            "message": message,
            "best_prompt": best_prompt,
            "worst_prompt": worst_prompt,
        }
    )

    return context
