from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django import http

from subhub import models

def _get_verify(verifies):
    for v in verifies:
        if v in ('sync', 'async'):
            return v
    raise KeyError('hub.verify is missing or not recognized')

@csrf_exempt
@require_POST
def hub(request):
    try:
        callback = request.POST['hub.callback']
        topic = request.POST['hub.topic']
        mode = request.POST['hub.mode']
        verify = _get_verify(request.POST.getlist('hub.verify'))
    except KeyError, e:
        return http.HttpResponseBadRequest(str(e))
    if mode not in dict(models.MODES):
        return http.HttpResponseBadRequest('Unknown hub.mode: %s' % mode)

    defaults = {
        'lease_seconds': (request.POST.get('hub.lease-seconds'), int),
        'secret': (request.POST.get('hub.secret'), str),
    }
    try:
        defaults = dict((k, c(v)) for k, (v, c) in defaults.items() if v is not None)
    except ValueError, e:
        return http.HttpResponseBadRequest(str(e))
    task, created = models.SubscriptionTask.objects.get_or_create(
        callback = callback,
        topic = topic,
        verify_token = request.POST.get('hub.verify_token', ''),
        mode = mode,
        defaults = defaults,
    )
    if verify == 'sync':
        result, description = task.verify()
        if result and description == 'verified':
            return http.HttpResponse('', status=204)
        else:
            return http.HttpResponseBadRequest('Verification failed: %s' % description)
    else:
        return http.HttpResponse('Subscription queued', status=202)
