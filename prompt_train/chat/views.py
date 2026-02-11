from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()


@login_required
def chat_room(request):
    return render(request, "chat/room.html")


@login_required
def conversations_list(request):
    conversations = (
        Conversation.objects.filter(participants=request.user)
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False)
                & ~Q(messages__user_id=request.user.id),
            ),
            last_message_time=Max("messages__timestamp"),
        )
        .prefetch_related("participants", "messages")
        .order_by("-last_message_time")
    )

    conversations_data = []
    for conv in conversations:
        other_user = conv.participants.exclude(id=request.user.id).first()
        last_message = conv.messages.last()

        conversations_data.append(
            {
                "conversation": conv,
                "other_user": other_user,
                "last_message": last_message.get_decrypted_content()
                if last_message
                else None,
                "unread_count": conv.unread_count,
            }
        )
    paginator = Paginator(conversations_data, 5)
    page = request.GET.get("page")

    try:
        conversations_page = paginator.page(page)
    except PageNotAnInteger:
        conversations_page = paginator.page(1)
    except EmptyPage:
        conversations_page = paginator.page(paginator.num_pages)

    return render(
        request, "chat/conversations_list.html", {"conversations": conversations_page}
    )


@login_required
def private_chat(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    if other_user == request.user:
        return redirect("chat:conversations_list")

    conversation = Conversation.get_or_create_conversation(request.user, other_user)

    return render(
        request,
        "chat/private_chat.html",
        {"other_user": other_user, "conversation": conversation},
    )


@login_required
def users_list(request):
    paginator = Paginator(User.objects.all(), 5)
    page = request.GET.get("page")

    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)

    return render(request, "chat/users_list.html", {"users": users_page})
