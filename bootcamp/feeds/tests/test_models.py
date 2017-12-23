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
            comments=0
        )

        self.feed2 = Feed.objects.create(
            user=self.user,
            post='Another text',
            likes=0,
            comments=0
        )
        self.feed3 = Feed.objects.create(
            user=self.user,
            post='Feed3 text',
            likes=0,
            comments=0
        )

        self.feed.comment(self.other_user, 'my comment')

        self.feed.retweet(self.other_user)
        self.feed2.retweet(self.other_user)

        like = Activity(activity_type=Activity.LIKE, feed=self.feed.id, user=self.other_user)
        like.save()
        self.user.profile.notify_liked(self.feed)

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

    def test_getFeeds_withFromFeed1(self):
        feeds = Feed.get_feeds(self.feed2.id)
        self.assertEquals(len(feeds), 2)
        self.assertTrue(self.feed in feeds)
        self.assertTrue(self.feed2 in feeds)

    def test_retweet_mustHaveOneRetweeter(self):
        self.assertEquals(1, self.feed.retweeters.count())
        self.assertEquals(self.other_user, self.feed.retweeters.first())

    def test_retweet_userCannotRetweetItsFeedException(self):
        try:
            self.feed.retweet(self.user)
            self.fail()
        except Exception:
            pass

    def test_retweet_alreadyRetweetted(self):
        try:
            self.feed.retweet(self.other_user)
            self.fail()
        except Exception:
            pass

    def test_removeRetweet_userCannotRemoveRetweetOfItsFeed(self):
        try:
            self.feed.remove_retweet(self.user)
            self.fail()
        except Exception:
            pass

    def test_removeRetweet_didNotRetweetedBeforeException(self):
        try:
            self.feed3.remove_retweet(self.other_user)
            self.fail()
        except Exception:
            pass

    def test_removeRetweet_retweetersMustBeEmpty(self):
        self.feed2.remove_retweet(self.other_user)
        self.assertEquals(0, self.feed2.retweeters.count())