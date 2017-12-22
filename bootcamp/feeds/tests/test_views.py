import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from bootcamp.feeds.models import Feed


class TestViews(TestCase):
    """
    Includes tests for all the functionality
    associated with Views
    """
    def setUp(self):
        self.client = Client()
        self.other_client = Client()
        self.user = get_user_model().objects.create_user(
            username='test_user',
            email='test@gmail.com',
            password='top_secret'
        )
        self.other_user = get_user_model().objects.create_user(
            username='other_test_user',
            email='other_test@gmail.com',
            password='top_secret'
        )
        self.client.login(username='test_user', password='top_secret')
        self.other_client.login(
            username='other_test_user', password='top_secret')
        self.feed = Feed.objects.create(
            user=self.user,
            post='A not so long text',
            likes=0,
            comments=0)
        self.feed_2 = Feed.objects.create(
            user=self.user,
            post='A not so long text 2',
            likes=0,
            comments=0)
        self.comment_text = 'my_comment'
        self.feed_2.comment(user=self.user, post=self.comment_text)

    def test_feed_view(self):
        request = self.client.get(reverse('feed', args=[self.feed.id]))
        self.assertEqual(request.status_code, 200)

    def test_load_page1_viewAllFeeds(self):
        response = self.client.get('/feeds/load/?page=1&feed_source=all', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.feed.post in response.content)
        self.assertTrue(self.feed_2.post in response.content)

    def test_load_page1_viewTestUserFeeds(self):
        response = self.client.get('/feeds/load/?page=1&feed_source=' + str(self.user.id), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.feed.post in response.content)

    def test_load_withoutPageNumber_BadRequest(self):
        response = self.client.get('/feeds/load/?feed_source=all', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 400)

    def test_load_emptyPage_NoFeed(self):
        response = self.client.get('/feeds/load/?page=10&feed_source=all', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertFalse(self.feed.post in response.content)

    def test_loadNew(self):
        response = self.client.get('/feeds/load_new/?last_feed=' + str(self.feed.id),
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.feed_2.post in response.content)

    def test_check(self):
        response = self.client.get('/feeds/check/?last_feed=' + str(self.feed.id) + '&feed_source=' + str(self.user.id), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '1')

    def test_post(self):
        response = self.client.post('/feeds/post/', { 'post': 'another_post', 'last_feed': str(self.feed.id) }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.feed_2.post in response.content)
        self.assertTrue('another_post' in response.content)

    def test_like(self):
        response = self.client.post('/feeds/like/', { 'feed': str(self.feed.id), 'last_feed': str(self.feed.id) }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '1')

    def test_dislike(self):
        self.client.post('/feeds/like/', {'feed': str(self.feed.id), 'last_feed': str(self.feed.id)},
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.post('/feeds/like/', {'feed': str(self.feed.id), 'last_feed': str(self.feed.id)},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '0')

    def test_getComment(self):
        response = self.client.get('/feeds/comment/?feed=' + str(self.feed_2.id), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.comment_text in response.content)

    def test_postComment(self):
        response = self.client.post('/feeds/comment/', { 'feed': str(self.feed.id), 'post': 'my_feed1_comment' }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue('my_feed1_comment' in response.content)

    def test_update(self):
        # TODO: Bug here
        response = self.client.get(
            '/feeds/update/?'
            'first_feed=' + str(self.feed_2.id) +
            '&last_feed=' + str(self.feed.id) +
            '&feed_source=' + str(self.user.id),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json.loads(response.content), {str(self.feed.id): {"likes": 0, "comments": 0}, str(self.feed_2.id): {"likes": 0, "comments": 1}})

    def test_trackComments_getFeed1Comments(self):
        response = self.client.get('/feeds/track_comments/?feed=' + str(self.feed_2.id), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(self.comment_text in response.content)


    def test_trackComments_NoComment(self):
        response = self.client.get('/feeds/track_comments/?feed=' + str(self.feed.id), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '')

    def test_remove_badRequest(self):
        response = self.client.post('/feeds/remove/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 400)

    def test_remove_forbidden(self):
        response = self.other_client.post('/feeds/remove/', {'feed': str(self.feed.id)}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 403)

    def test_remove_successfully(self):
        self.client.post('/feeds/like/', { 'feed': str(self.feed.id), 'last_feed': str(self.feed.id) }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response = self.client.post('/feeds/remove/', {'feed': str(self.feed.id)}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, '')
