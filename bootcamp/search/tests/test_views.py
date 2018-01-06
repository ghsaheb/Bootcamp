from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from bootcamp.articles.models import Article
from bootcamp.feeds.models import Feed
from bootcamp.questions.models import Question


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
        self.title = 'A really nice to-be title'
        self.content = '''This is a really good content, just if somebody published
        it, that would be awesome, but no, nobody wants to publish it, because
        they know this is just a test, and you know than nobody wants to
        publish a test, just a test; everybody always wants the real deal.'''
        self.article = Article.objects.create(
            create_user=self.user, title='A really nice title',
            content=self.content, tags='list, lists', status='P')

        self.article_2 = Article.objects.create(create_user=self.other_user, title='A bad title',
                                                content="Bad content", tags='bad', status='P')

        self.feed = Feed.objects.create(
            user=self.user,
            post='This is a feed',
            likes=0,
            spams=0,
            comments=0)

        self.feed_2 = Feed.objects.create(
            user=self.other_user,
            post='This is another feed',
            likes=0,
            spams=0,
            comments=0)

        self.question_one = Question.objects.create(
            user=self.user, title='This is a sample question',
            description='This is a sample question description',
            tags='test1,test2')
        self.question_two = Question.objects.create(
            user=self.user,
            title='A Short Title',
            description='''This is a really good content, just if somebody
            published it, that would be awesome, but no, nobody wants to
            publish it, because they know this is just a test, and you
            know than nobody wants to publish a test, just a test;
            everybody always wants the real deal.''',
            favorites=0,
            has_accepted_answer=True
        )

    def test_search_noqeury_redirectToSearchPage(self):
        response = self.client.get('/search')
        self.assertRedirects(response, '/search/', 301)

    def test_search_queryWithZeroLength_redirectToSearchPage(self):
        response = self.client.get('/search/?q=')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/search/', status_code=302)

    def test_search_queryWithoutSearchType_viewAllFeeds(self):
        response = self.client.get('/search/?q=a')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.feed.post in response.content)
        self.assertTrue(self.feed_2.post in response.content)

    def test_search_queryWithArticleSearchType_viewAllArticles(self):
        response = self.client.get('/search/?q=a&type=articles')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.article.title in response.content)
        self.assertTrue(self.article_2.title in response.content)

    def test_autocomplete_question_suggestions(self):
        search_term = "short"
        question_search_response = self.client.get(
            '/autocomplete/?term=' + search_term,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        question_search_suggestions_dict = question_search_response.json()
        self.assertEqual(
            question_search_suggestions_dict[0]['value'], "A Short Title")

    def test_autocomplete_article_suggestions(self):
        search_term = "title"
        question_search_response = self.client.get(
            '/autocomplete/?term=' + search_term,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        question_search_suggestions_dict = question_search_response.json()
        self.assertEqual(
            question_search_suggestions_dict[0]['value'], "A bad title")

    def test_autocomplete_user_suggestions(self):
        search_term = "other"
        question_search_response = self.client.get(
            '/autocomplete/?term=' + search_term,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        question_search_suggestions_dict = question_search_response.json()
        self.assertEqual(
            question_search_suggestions_dict[0]['value'], "other_test_user")
