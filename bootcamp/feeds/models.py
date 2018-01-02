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
    source_feed = models.ForeignKey('Feed', null=True, blank=True, related_name='retweet_source_feed')

    class Meta:
        verbose_name = _('Feed')
        verbose_name_plural = _('Feeds')
        ordering = ('-date',)

    def __str__(self):
        if self.is_retweet():
            return self.get_source_feed().__str__()

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
        if self.is_retweet():
            return self.get_source_feed().get_comments()

        return Feed.objects.filter(parent=self).order_by('date')

    def calculate_likes(self):
        if self.is_retweet():
            return self.get_source_feed().calculate_likes()

        likes = Activity.objects.filter(activity_type=Activity.LIKE,
                                        feed=self.pk).count()
        self.likes = likes
        self.save()
        return self.likes

    def get_likes(self):
        if self.is_retweet():
            return self.get_source_feed().get_likes()

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
        if self.is_retweet():
            return self.get_source_feed().calculate_comments()

        self.comments = Feed.objects.filter(parent=self).count()
        self.save()
        return self.comments

    def comment(self, user, post):
        if self.is_retweet():
            return self.get_source_feed().comment(user, post)

        feed_comment = Feed(user=user, post=post, parent=self)
        feed_comment.save()
        self.comments = Feed.objects.filter(parent=self).count()
        self.save()
        return feed_comment

    def linkfy_post(self):
        if self.is_retweet():
            return self.get_source_feed().linkfy_post()

        return bleach.linkify(escape(self.post))

    def retweet(self, user):
        if self.is_retweet():
            return self.get_source_feed().retweet(user)

        retweet_feed = Feed(user=user, source_feed=self)
        retweet_feed.save()

        return retweet_feed

    def is_retweet(self):
        return self.source_feed is not None

    def get_source_feed(self):
        if self.is_retweet():
            return self.source_feed.get_source_feed()

        return self

    def get_post(self):
        if self.is_retweet():
            return self.get_source_feed().get_post()

        return self.post

    def get_likes_count(self):
        if self.is_retweet():
            return self.get_source_feed().get_likes_count()

        return self.likes

    def get_comments_count(self):
        if self.is_retweet():
            return self.get_source_feed().get_comments_count()

        return self.comments

    def get_retweets_count(self):
        if self.is_retweet():
            return self.get_source_feed().get_retweets_count()

        return Feed.objects.filter(source_feed=self).count()
