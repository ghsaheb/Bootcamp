from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from friendship.models import Friend, FriendshipRequest


@login_required
def send_request(request):
    to_username = request.GET.get('username')
    to_user = get_object_or_404(User, username=to_username)
    request = Friend.objects.add_friend(from_user=request.user, to_user=to_user)
    to_user.profile.notify_friendship_request(request)
    return redirect('/' + to_username)

@login_required
def accept_request(request):
    friendship_request_id = request.GET.get('id')
    friendship_request = FriendshipRequest.objects.get(pk=friendship_request_id)

    if friendship_request.to_user == request.user:
        friendship_request.accept()
        friendship_request.from_user.profile.notify_friendship_request_accept(friendship_request)
        return redirect('/' + friendship_request.from_user.username)
    else:
        return HttpResponseBadRequest()

@login_required
def reject_request(request):
    friendship_request_id = request.GET.get('id')
    friendship_request = FriendshipRequest.objects.get(pk=friendship_request_id)
    from_user = friendship_request.from_user
    if friendship_request.to_user == request.user:
        friendship_request.reject()
        friendship_request.delete()
        friendship_request.from_user.profile.notify_friendship_request_reject(friendship_request)
        return redirect('/' + from_user.username)
    else:
        return HttpResponseBadRequest()