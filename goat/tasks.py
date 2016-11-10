from __future__ import absolute_import

import os
from django.conf import settings
from celery import Celery
app = Celery('goat')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.update(BROKER_URL=os.environ.get('REDISTOGO_URL', 'redis://'),
                CELERY_RESULT_BACKEND=os.environ.get('REDISTOGO_URL', 'redis://'))

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
    tasks = [search.s(user, auth, params, results.id) for auth in authorities]
    chord(tasks)(register_results.s())
    return results.id


@app.task(name='goat.tasks.search', bind=True)
def search(self, user, authority, params, result_id):
    """
    Perform a search using a single :class:`.Authority` instance.

    Parameters
    ----------
    user : :class:`django.contrib.auth.models.User`
    authority : :class:`goat.models.Authority`
    params : dict
    result_id : int
        PK-identifier for :class:`goat.models.SearchResultSet`\.

    Returns
    -------
    concepts : list
        A list of :class:`goat.models.Concept` instances.
    result_id : int
        PK-identifier for :class:`goat.models.SearchResultSet`\.
    """
    concepts = []

    results = authority.search(params)

    for result in results:
        if result.concept_type:
            concept_type, _ = Concept.objects.get_or_create(
                identifier=result.concept_type,
                defaults={
                    'added_by': user,
                    'authority': authority
                }
            )
        else:
            concept_type = None
        concepts.append(
            Concept.objects.get_or_create(
                identifier=result.identifier,
                defaults={
                    'added_by': user,
                    'name': result.name,
                    'description': result.description,
                    'concept_type': concept_type,
                    'authority': authority
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
