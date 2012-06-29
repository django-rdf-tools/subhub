# -*- coding:utf-8 -*-
from django.contrib import admin

from subhub import models

admin.site.register(models.Subscription,
    list_display = ['topic', 'callback', 'expires'],
    ordering = ['topic', 'callback'],
    readonly_fields = ['callback', 'verify_token', 'secret'],
)

admin.site.register(models.SubscriptionTask,
    list_display = ['topic', 'callback', 'mode', 'ttl'],
    ordering = ['id'],
    readonly_fields = ['callback', 'verify_token', 'mode'],
)

admin.site.register(models.DistributionTask,
    list_display = ['subscription', 'entry_id'],
    ordering = ['subscription'],
    readonly_fields = ['subscription', 'entry_id'],
)
