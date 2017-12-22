from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from bootcamp.feeds.models import Feed


class TestSenarios(TestCase):

    def setUp(self):
        self.aliClient = Client()
        self.poopakClient = Client()
        self.ali = get_user_model().objects.create_user(
            username='ali',
            email='ali@gmail.com',
            password='ali'
        )
        self.poopak = get_user_model().objects.create_user(
            username='poopak',
            email='poopak@gmail.com',
            password='poopak'
        )

    # Ali logged in
    # Ali sends a post (feed)
    # Ali logged out
    # Poopak logged in
    # Poopak likes Ali's post
    # Poopak sends a comment on Ali's post
    # Ali logged in
    # Ali sends a comment on Poopak's comment
    # Ali logged out
    # Poopak logged out

    def test_senario1(self):
        self.aliLoggedIn()
        self.aliSendsPost('Who loves me?')
        self.aliLoggedOut()
        self.alisFeed = Feed.get_feeds().filter(user__id=self.ali.id)[0]
        self.poopakLoggedIn()
        self.poopakLikesAlisPost()
        self.poopakSendsCommentOnAlisPost('I love you baby!')
        self.aliLoggedIn()
        self.aliSendsCommentOnPoopaksComment('+989355246329')
        self.aliLoggedOut()
        self.poopakLoggedOut()

        alisFeeds = Feed.get_feeds().filter(user__id=self.ali.id)
        self.assertEquals(len(alisFeeds), 1)
        self.assertEquals(alisFeeds[0].post, 'Who loves me?')
        self.assertEquals(alisFeeds[0].calculate_likes(), 1)
        self.assertEqual(alisFeeds[0].get_likers()[0], self.poopak)
        self.assertEqual(alisFeeds[0].get_comments()[0].post, 'I love you baby!');
        self.assertEqual(alisFeeds[0].get_comments()[1].post, '+989355246329');

    def aliLoggedIn(self):
        self.aliClient.login(username='ali', password='ali')

    def aliSendsPost(self, message):
        response = self.aliClient.post('/feeds/post/', { 'post': message, 'last_feed': str(0) }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def aliLoggedOut(self):
        self.aliClient.logout()

    def poopakLoggedOut(self):
        self.poopakClient.logout()

    def poopakLoggedIn(self):
        self.poopakClient.login(username='poopak', password='poopak')

    def poopakLikesAlisPost(self):
        response = self.poopakClient.post('/feeds/like/', { 'feed': str(self.alisFeed.id), 'last_feed': str(self.alisFeed.id) }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def poopakSendsCommentOnAlisPost(self, message):
        response = self.poopakClient.post('/feeds/comment/', { 'feed': str(self.alisFeed.id), 'post': message }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def aliSendsCommentOnPoopaksComment(self, message):
        response = self.aliClient.post('/feeds/comment/', { 'feed': str(self.alisFeed.id), 'post': message }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
