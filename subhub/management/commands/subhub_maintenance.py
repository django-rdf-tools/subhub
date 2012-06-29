from datetime import datetime, timedelta
from optparse import make_option
import logging

from django.core.management.base import NoArgsCommand, CommandError

log = logging.getLogger('subhub.maintenance')

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('-d', '--distribute',
            action = 'store_true',
            dest = 'distribute',
            default = False,
            help = u'Process content distribution tasks',
        ),
        make_option('-s', '--subscribe',
            action = 'store_true',
            dest = 'subscribe',
            default = False,
            help = u'Process subscriptions (verification, expiration, refreshing)',
        ),
    )
    help = u'SubHub maintenance'

    def handle_noargs(self, subscribe, distribute, **base_options):
        if not distribute and not subscribe:
            raise CommandError('Nothing to do: no options specified')

        from subhub import models, utils
        log.info('Start')

        if subscribe:
            try:
                log.info('Expiring and refreshing subscriptions...')
                models.Subscription.objects.process(log=log)
            except utils.LockError, e:
                log.warning(str(e))

            try:
                log.info('Processing verification queue...')
                models.SubscriptionTask.objects.process(log=log)
            except utils.LockError, e:
                log.warning(str(e))


        if distribute:
            try:
                log.info('Processing distribution...')
                models.DistributionTask.objects.process(log=log)
            except utils.LockError, e:
                log.warning(str(e))

        log.info('Done')
