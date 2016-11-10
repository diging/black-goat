from __future__ import absolute_import

import os
from django.conf import settings
from celery import Celery
app = Celery('goat')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.update(BROKER_URL=os.environ.get('REDIS_URL', 'redis://'),
                CELERY_RESULT_BACKEND=os.environ.get('REDIS_URL', 'redis://'))

from celery import chord

from goat.models import *


@app.task(name='goat.tasks.orchestrate_search', bind=True)
def orchestrate_search(self, user, authorities, params):
    """
    Farm out search tasks (in a chord) to each of the :class:`.Authority`
    instances in ``authorities``.
    """

    results = SearchResultSet.objects.create(added_by=user,
                                             task_id=self.request.id,
                                             state=SearchResultSet.PENDING)
    tasks = [search.s(auth, params, results.id) for auth in authorities]
    chord(tasks)(register_results.s())
    return results.id


@app.task(name='goat.tasks.search', bind=True)
def search(self, authority, params, result_id):
    """
    Perform a search for a single :class:`.Authority` instance.
    """
    concepts = []

    results = authority.search(params)

    for result in results:
        if result.concept_type:
            concept_type, _ = Concept.objects.get_or_create(identifier=result.concept_type)
            concepts.append(
                Concept.objects.get_or_create(
                    identifier=result.identifier,
                    defaults={
                        'name': result.name,
                        'description': result.description,
                        'concept_type': concept_type,
                    }
                )[0]
            )
    return concepts, result_id


@app.task(name='goat.tasks.register_results', bind=True)
def register_results(self, results):
    if not results:
        return

    result_set = None
    for concepts, result_id in results:
        if not result_set:
            result_set = SearchResultSet.objects.get(pk=result_id)
        result_set.results.add(*concepts)
    result_set.state = SearchResultSet.SUCCESS
    result_set.save()
