from django.conf.urls import url

from bootcamp.friends import views

urlpatterns = [
    url(r'^send_request$', views.send_request, name='send_request'),
    url(r'^accept_request$', views.accept_request, name='accept_request'),
    url(r'^reject_request$', views.reject_request, name='reject_request'),
]
