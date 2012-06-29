# -*- coding:utf-8 -*-
from urlparse import urlsplit
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError
import socket
import os
import tempfile
import threading, Queue

import httplib2
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site


class FeedError(Exception):
    pass


HTTP_TIMEOUT = 10
HTTP_ERRORS = (IOError, httplib2.HttpLib2Error, socket.error)
FEED_ERRORS = (ExpatError, FeedError)

NS = '{http://www.w3.org/2005/Atom}'
def _ns_path(path):
    '''
    Adds Atom namespace to all element names in path.
    '''
    return '/'.join(c and '%s%s' % (NS, c) for c in path.split('/'))

class AtomElement(object):
    def __init__(self, element):
        self.element = element

    def findall(self, path):
        return map(AtomElement, self.element.findall(_ns_path(path)))

    def find(self, path):
        element = self.element.find(_ns_path(path))
        return AtomElement(element) if element is not None else element

    def remove(self, atom_element):
        return self.element.remove(atom_element.element)

    def __getattr__(self, name):
        return getattr(self.element, name)


class Atom(object):
    def __init__(self, root):
        self.root = AtomElement(root)

    def __str__(self):
        return '%s\n%s' % (
            '<%xml version="1.0" encoding="utf-8"%>',
            ET.tostring(self.root.element, encoding='utf-8'),
        )

    def link(self, rel):
        for link in self.root.findall('link'):
            if link.attrib['rel'] == rel:
                return link.attrib['href']


def _normalize_host(host):
    if host.endswith(':80'):
        host = host[:-3]
    return host.lower()

def parse_atom(url, cache=None):
    '''
    Tries to parse URL's content as an Atom feed. Returns parsed Atom object
    if successful or raises one of the FEED_ERRORS or HTTP_ERRORS exceptions.
    '''
    if cache is not None and url in cache:
        return cache[url]

    scheme, host, path, query, fragment = urlsplit(url)
    localhost = Site.objects.get_current().domain
    if _normalize_host(host) != _normalize_host(localhost):
        raise FeedError('Topic is not local to %s' % localhost)
    h = httplib2.Http(timeout=HTTP_TIMEOUT)
    response, body = h.request(url, 'GET')
    if response.status >= 300:
        raise httplib2.HttpLib2Error(response.status, body)
    if not response['content-type'].startswith('application/atom+xml'):
        raise FeedError('Bad content type: %s' % response['Content-type'])
    atom = Atom(ET.XML(body))
    if atom.root.find('id') is None:
        raise FeedError('No <atom:id/> element in feed')
    if atom.link('self') is None:
        raise FeedError('No <atom:link rel="self"/> element in feed')
    scheme, host, path, query, fragment = urlsplit(atom.link('hub') or '')
    if (host, path) != (localhost, reverse('subhub-hub')):
        raise FeedError('<atom:link rel="hub"/> is missing or is not mine')

    if cache is not None:
        cache[url] = atom
    return atom


class LockError(Exception):
    pass


def lock(name):
    filename = os.path.join(tempfile.gettempdir(), 'subhub.%s.lock' % name)
    try:
        os.open(filename, os.O_EXCL | os.O_CREAT)
    except OSError:
        raise LockError('Lock "%s" exists' % filename)

def unlock(name):
    filename = os.path.join(tempfile.gettempdir(), 'subhub.%s.lock' % name)
    os.remove(filename)


def pool(func, args_sequence, thread_count=10):
    '''
    Applies `func` to each of set of args given in `args_sequence` using a pool
    of worker threads.

    Returns results as a deque of tuples in the form (result, args).
    '''
    args_queue = Queue.Queue()
    [args_queue.put(args) for args in args_sequence]
    results = Queue.Queue()

    def target():
        try:
            while True:
                args = args_queue.get_nowait()
                results.put((func(*args), args))
        except Queue.Empty:
            pass

    threads = [threading.Thread(target=target) for i in range(thread_count)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    return results.queue
