from django.conf.urls.defaults import patterns, url

from subhub import views

urlpatterns = patterns('',
    url(r'^$', views.hub, name='subhub-hub'),
)
