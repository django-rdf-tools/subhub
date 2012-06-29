======
SubHub
======

SubHub is a Django application that implements a `PubSubHubBub`_ hub. Think
of it as a push mechanism that your personal site uses to notify subscribers
about changes in feeds that your site publishes.

.. note:: SubHub works only for Atom feeds. Which you should use anyway since
today there are no more reasons left to use actual RSS format for feeds.

This hub is not a standalone daemon that runs alongside your Django project.
It works as a library code sending notifications whenever you hit a "Publish"
button. It does, however, requires a cron job to process pending subscriptions
and failed notifications.

.. _PubSubHubBub: http://code.google.com/p/pubsubhubbub/


Installation
============

1. Install SubHub using your favorite package manager or simply with ``python
setup.py install``.

2. Include it "subhub" into INSTALLED_APPS in your Django settings and run
``./manage.py syncdb`` to create new tables.

3. Include SubHub urls into your project's urlconf under some sensible name::

    urlpatterns = patterns('',
        ...
        (r'^hub/', include('subhub.urls')),
    )

4. Setup a cron job that will process pending subscriptions and distribute
failed notifications::

    # Process subscriptions every 3 hours
    0    */3  * * *   user  /path/to/manage.py subhub_maintenance --subscribe

    # Distribute notifications every 15 minutes
    */15 *    * * *   user  /path/to/manage.py subhub_maintenance --distribute


Announcing your hub
===================

In order to tell your potential subscribers that your feeds use PubSubHubBub
notifications you should include a link to a SubHub subscription view into
your Atom feeds. It looks a bit heavy but don't let it scare you off!

First thing to do is to subclass Django's built-in Atom feed generator and
teach it to look for hub links defined in your specific feed definitions::

    from django.utils.feedgenerator import Atom1Feed

    class HubAtom1Feed(Atom1Feed):
        def add_root_elements(self, handler):
            super(HubAtom1Feed, self).add_root_elements(handler)
            hub_link = self.feed.get('hub_link')
            if hub_link is not None:
                handler.addQuickElement(u'link', '', {
                    u'rel': u'hub',
                    u'href': hub_link,
                })

Then in each your feed for which you want to use notifications define a link::

    from django.contrib.syndication import views

    class MyBlogFeed(views.Feed):
        feed_type = HubAtom1Feed

        def feed_extra_kwargs(self, obj):
            return {
                'hub_link': absolute_url(reverse('subhub-hub')),
            }

Chances are that you already have a function like ``absolute_url`` in your
project. It should make an URL absolute adding a scheme and a domain.


Publishing new and changed items
================================

To publish newly created or updated post you call function ``subhub.publish``
passing it two parameters:

- a list of feeds ("topics" in PubSubHubBub parlance) that this post appears in
- an entry_id for a post which in most cases is its absolute URL

Example::

    import subhub

    class Post(models.Model):

        def save(self, **kwargs):
            super(Post, self).save(**kwargs)
            if self.published:
                if transaction.is_managed():
                    transaction.commit()
                topics = ['/blog/feed/'] # don't hardcode URLs, use 'reverse'
                subhub.publish(
                    [absolute_url(t) for t in topics],
                    absolute_url(self.get_absolute_url()),
                )

You can call "publish" from anywhere you find suitable. Just make sure that
before the call you commit a DB transaction if you use one. This is needed
because SubHub will make a separate HTTP request into your own server to fetch
an updated feed.
