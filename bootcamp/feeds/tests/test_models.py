from django.contrib.auth import get_user_model
from django.test import TestCase

from bootcamp.activities.models import Activity
from bootcamp.feeds.models import Feed


class TestModels(TestCase):
    """TestCase class to test the models functionality
    """

    def setUp(self):
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
        self.feed = Feed.objects.create(
            user=self.user,
            post='A not so long text',
            likes=0,
            spams=0,
            comments=0
        )
        self.feed2 = Feed.objects.create(
            user=self.user,
            post='Another text',
            likes=0,
            spams=0,
            comments=0
        )

        self.feed.comment(self.other_user, 'my comment')

        like = Activity(activity_type=Activity.LIKE, feed=self.feed.id, user=self.other_user)
        like.save()
        self.user.profile.notify_liked(self.feed)

        spam = Activity(activity_type=Activity.SPAM, feed=self.feed.id, user=self.other_user)
        spam.save()
        self.user.profile.notify_spamed(self.feed)


    def test_instance_values(self):
        self.assertTrue(isinstance(self.feed, Feed))

    def test_feed_return_value(self):
        self.assertEqual(str(self.feed), 'A not so long text')

    def test_calculateComments(self):
        self.assertEquals(self.feed.calculate_comments(), 1)

    def test_getLikers(self):
        likers = self.feed.get_likers()
        self.assertEquals(len(likers), 1)
        self.assertEquals(likers[0], self.other_user)

    def test_getSpamers(self):
        spamers = self.feed.get_spammers()
        self.assertEquals(len(spamers), 1)
        self.assertEquals(spamers[0], self.other_user)

    def test_getFeeds_withFromFeed1(self):
        feeds = Feed.get_feeds(self.feed2.id)
        self.assertEquals(len(feeds), 2)
        self.assertTrue(self.feed in feeds)
        self.assertTrue(self.feed2 in feeds)

