import random
from django.db import transaction
from .models import Prompt 
from .ai_func import evaluate_prompt_quality



def get_random_high_rated_prompt() -> Prompt | None:
    high_rated_prompts = Prompt.objects.filter(rate__gte=7)
    
    if not high_rated_prompts.exists():
        return None
    
    return random.choice(high_rated_prompts)


def validate_user_prompt(user_prompt_text: str) -> tuple[bool, str | None]:
    if not user_prompt_text:
        return False, "Будь ласка, введіть промпт."
    
    if len(user_prompt_text) > 500:
        return False, "Промпт має бути не більше 500 символів."
    
    return True, None


def calculate_challenge_result(user_rate: float, challenge_rate: int) -> tuple[str, str]:
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
        user.save(update_fields=['exp', 'points'])


def create_user_prompt(user_prompt_text: str, user) -> tuple[float, str, str]:
    
    user_rate, improvement_hint, refined_prompt = evaluate_prompt_quality(user_prompt_text)
    
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
        context['error'] = "Поки що немає промптів з оцінкою 7+. Спробуйте пізніше!"
        return context
    
    request.session['challenge_prompt_id'] = challenge_prompt.id
    context['challenge_prompt'] = challenge_prompt
    
    return context


def handle_challenge_post(request) -> dict:
    context = {}
    
    user_prompt_text = request.POST.get("prompt", "").strip()
    challenge_prompt_id = request.session.get('challenge_prompt_id')
    
    if not challenge_prompt_id:
        return None  
    
    try:
        challenge_prompt = Prompt.objects.get(id=challenge_prompt_id)
    except Prompt.DoesNotExist:
        return None   
    
    is_valid, error_message = validate_user_prompt(user_prompt_text)
    if not is_valid:
        context['error'] = error_message
        context['challenge_prompt'] = challenge_prompt
        return context
    
    user_rate, improvement_hint, refined_prompt = create_user_prompt(
        user_prompt_text, 
        request.user
    )
    
    result, message = calculate_challenge_result(user_rate, challenge_prompt.rate)
    
    award_user_points(request.user, result)
    
    if 'challenge_prompt_id' in request.session:
        del request.session['challenge_prompt_id']
    
    context.update({
        'result': result,
        'message': message,
        'user_prompt': user_prompt_text,
        'user_rate': user_rate,
        'challenge_prompt': challenge_prompt,
        'challenge_rate': challenge_prompt.rate,
        'improvement_hint': improvement_hint,
        'refined_prompt': refined_prompt,
    })
    
    return context
