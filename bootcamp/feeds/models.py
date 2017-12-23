from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

import bleach
from bootcamp.activities.models import Activity

@python_2_unicode_compatible
class Feed(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    post = models.TextField(max_length=255)
    parent = models.ForeignKey('Feed', null=True, blank=True)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    retweeters = models.ManyToManyField(User, through='Retweet', related_name='Retweets')

    class Meta:
        verbose_name = _('Feed')
        verbose_name_plural = _('Feeds')
        ordering = ('-date',)

    def __str__(self):
        return self.post

    @staticmethod
    def get_feeds(from_feed=None):
        if from_feed is not None:
            feeds = Feed.objects.filter(parent=None, id__lte=from_feed)
        else:
            feeds = Feed.objects.filter(parent=None)
        return feeds

    @staticmethod
    def get_feeds_after(feed):
        feeds = Feed.objects.filter(parent=None, id__gt=feed)
        return feeds

    def get_comments(self):
        return Feed.objects.filter(parent=self).order_by('date')

    def calculate_likes(self):
        likes = Activity.objects.filter(activity_type=Activity.LIKE,
                                        feed=self.pk).count()
        self.likes = likes
        self.save()
        return self.likes

    def get_likes(self):
        likes = Activity.objects.filter(activity_type=Activity.LIKE,
                                        feed=self.pk)
        return likes

    def get_likers(self):
        likes = self.get_likes()
        likers = []
        for like in likes:
            likers.append(like.user)
        return likers

    def calculate_comments(self):
        self.comments = Feed.objects.filter(parent=self).count()
        self.save()
        return self.comments

    def comment(self, user, post):
        feed_comment = Feed(user=user, post=post, parent=self)
        feed_comment.save()
        self.comments = Feed.objects.filter(parent=self).count()
        self.save()
        return feed_comment

    def linkfy_post(self):
        return bleach.linkify(escape(self.post))

    def retweet(self, user):
        if self.user == user:
            raise Exception("Feed owner cannot retweet it's feed.")
        if Retweet.objects.filter(user__id=user.id, feed__id=self.id).count() > 0:
            raise Exception("User already retweetted current feed.")
        ret = Retweet()
        ret.user = user
        ret.feed = self
        ret.save()

    def remove_retweet(self, user):
        if self.user == user:
            raise Exception("Invalid action.")
        if Retweet.objects.filter(user__id=user.id, feed__id=self.id).count() == 0:
            raise Exception("User didn't retweetted current feed before.")
        Retweet.objects.filter(user__id=user.id, feed__id=self.id).delete()

class Retweet(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    feed = models.ForeignKey(Feed)

    class Meta:
        verbose_name = _('Retweet')
        verbose_name_plural = _('Retweets')
        ordering = ('-date',)
