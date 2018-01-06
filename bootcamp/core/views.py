import os
import json

from PIL import Image

from django.conf import settings as django_settings
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render

from bootcamp.core.forms import ChangePasswordForm, ProfileForm
from bootcamp.feeds.views import FEEDS_NUM_PAGES, feeds
from bootcamp.feeds.models import Feed
from bootcamp.articles.models import Article, ArticleComment
from bootcamp.questions.models import Question, Answer
from bootcamp.activities.models import Activity
from bootcamp.messenger.models import Message

from friendship.models import Friend, Follow, FriendshipRequest, FriendshipManager

def home(request):
    if request.user.is_authenticated():
        return feeds(request)
    else:
        return render(request, 'core/cover.html')


@login_required
def network(request):
    users_list = User.objects.filter(is_active=True).order_by('username')
    paginator = Paginator(users_list, 100)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)

    except PageNotAnInteger:
        users = paginator.page(1)

    except EmptyPage:  # pragma: no cover
        users = paginator.page(paginator.num_pages)

    return render(request, 'core/network.html', {'users': users})


@login_required
def profile(request, username):
    page_user = get_object_or_404(User, username=username)
    all_feeds = Feed.get_feeds().filter(user=page_user)
    paginator = Paginator(all_feeds, FEEDS_NUM_PAGES)
    feeds = paginator.page(1)
    from_feed = -1
    if feeds:  # pragma: no cover
        from_feed = feeds[0].id

    feeds_count = Feed.objects.filter(user=page_user).count()
    article_count = Article.objects.filter(create_user=page_user).count()
    article_comment_count = ArticleComment.objects.filter(
        user=page_user).count()
    question_count = Question.objects.filter(user=page_user).count()
    answer_count = Answer.objects.filter(user=page_user).count()
    activity_count = Activity.objects.filter(user=page_user).count()
    messages_count = Message.objects.filter(
        Q(from_user=page_user) | Q(user=page_user)).count()
    data, datepoints = Activity.daily_activity(page_user)

    are_friends = Friend.objects.are_friends(request.user, page_user)
    has_friendship_request_to_page_user = FriendshipRequest.objects.filter(from_user=request.user, to_user=page_user).count() != 0
    friendship_request_from_page_user = FriendshipRequest.objects.filter(from_user=page_user, to_user=request.user).first()
    has_friendship_request_from_page_user = friendship_request_from_page_user is not None

    is_friendship_request_enabled = (request.user != page_user) and \
            not has_friendship_request_to_page_user and \
            not has_friendship_request_from_page_user and \
            not are_friends

    data = {
        'page_user': page_user,
        'feeds_count': feeds_count,
        'article_count': article_count,
        'article_comment_count': article_comment_count,
        'question_count': question_count,
        'global_interactions': activity_count + article_comment_count + answer_count + messages_count,  # noqa: E501
        'answer_count': answer_count,
        'bar_data': [
            feeds_count, article_count, article_comment_count, question_count,
            answer_count, activity_count],
        'bar_labels': json.dumps('["Feeds", "Articles", "Comments", "Questions", "Answers", "Activities"]'),  # noqa: E501
        'line_labels': datepoints,
        'line_data': data,
        'feeds': feeds,
        'from_feed': from_feed,
        'page': 1,
        'is_frienship_request_enabled': is_friendship_request_enabled,
        'are_friends': are_friends,
        'has_friendship_request_to_page_user': has_friendship_request_to_page_user,
        'has_friendship_request_from_page_user': has_friendship_request_from_page_user,
        'friendship_request_from_page_user': friendship_request_from_page_user
        }
    return render(request, 'core/profile.html', data)


@login_required
def settings(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.profile.job_title = form.cleaned_data.get('job_title')
            user.profile.birth_date = form.cleaned_data.get('birth_date')
            user.email = form.cleaned_data.get('email')
            user.profile.url = form.cleaned_data.get('url')
            user.profile.location = form.cleaned_data.get('location')
            user.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 'Your profile was successfully edited.')

    else:
        form = ProfileForm(instance=user, initial={
            'job_title': user.profile.job_title,
            'birth_date': user.profile.birth_date,
            'url': user.profile.url,
            'location': user.profile.location
            })

    return render(request, 'core/settings.html', {'form': form})


@login_required
def picture(request):
    uploaded_picture = False
    try:
        if request.GET.get('upload_picture') == 'uploaded':
            uploaded_picture = True

    except Exception:  # pragma: no cover
        pass

    return render(request, 'core/picture.html',
                  {'uploaded_picture': uploaded_picture})


@login_required
def password(request):
    user = request.user
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data.get('new_password')
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            messages.add_message(request, messages.SUCCESS,
                                 'Your password was successfully changed.')
            return redirect('password')

    else:
        form = ChangePasswordForm(instance=user)

    return render(request, 'core/password.html', {'form': form})


@login_required
def upload_picture(request):
    try:
        profile_pictures = django_settings.MEDIA_ROOT + '/profile_pictures/'
        if not os.path.exists(profile_pictures):
            os.makedirs(profile_pictures)
        f = request.FILES['picture']
        filename = profile_pictures + request.user.username + '_tmp.jpg'
        with open(filename, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        im = Image.open(filename)
        width, height = im.size
        if width > 350:
            new_width = 350
            new_height = (height * 350) / width
            new_size = new_width, new_height
            im.thumbnail(new_size, Image.ANTIALIAS)
            im.save(filename)

        return redirect('/settings/picture/?upload_picture=uploaded')

    except Exception:
        return redirect('/settings/picture/')


@login_required
def save_uploaded_picture(request):
    try:
        x = int(request.POST.get('x'))
        y = int(request.POST.get('y'))
        w = int(request.POST.get('w'))
        h = int(request.POST.get('h'))
        tmp_filename = django_settings.MEDIA_ROOT + '/profile_pictures/' +\
            request.user.username + '_tmp.jpg'
        filename = django_settings.MEDIA_ROOT + '/profile_pictures/' +\
            request.user.username + '.jpg'
        im = Image.open(tmp_filename)
        cropped_im = im.crop((x, y, w+x, h+y))
        cropped_im.thumbnail((200, 200), Image.ANTIALIAS)
        cropped_im.save(filename)
        os.remove(tmp_filename)

    except Exception:
        pass

    return redirect('/settings/picture/')
