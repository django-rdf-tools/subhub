def publish(topics, entry_id, process=True):
    '''
    Publish an update to subscribed clients.

    - `topics`: a list of absolute URLs for topics
    - `entry_id`: atom:id of the updated entry
    - `process`: a flag to force the immediate (blocking) processing of
       all wating updates
    '''
    from subhub.models import DistributionTask
    for topic in topics:
        DistributionTask.objects.add(topic, entry_id)
    if process:
        DistributionTask.objects.process()
