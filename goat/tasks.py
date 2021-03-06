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
from django.contrib.auth.models import User
from goat.models import *
import urllib


@app.task(name='goat.tasks.orchestrate_search', bind=True)
def orchestrate_search(self, user_id, authority_ids, params):
    """
    Farm out search tasks (in a chord) to each of the :class:`.Authority`
    instances in ``authorities``.
    """
    # We keep track of the parameters so that we don't end up running the same
    #  search several times in a row.
    params_serialized = urllib.urlencode(params)
    user = User.objects.get(pk=user_id)
    authorities = Authority.objects.filter(pk__in=authority_ids)

    authorities = filter(lambda a: a.configuration is not None, authorities)

    results = SearchResultSet.objects.create(added_by=user,
                                             task_id=self.request.id,
                                             state=SearchResultSet.PENDING,
                                             parameters=params_serialized)
    tasks = [search.s(user.id, auth.id, params, results.id) for auth in authorities]
    chord(tasks)(register_results.s())
    return results.id


@app.task(name='goat.tasks.search', bind=True)
def search(self, user_id, authority_id, params, result_id):
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

    user = User.objects.get(pk=user_id)
    authority = Authority.objects.get(pk=authority_id)
    concepts = []
    results = authority.search(params)

    for result in results:
        identities = result.extra.pop('identities', None)
        if getattr(result, 'concept_type', None):
            try:
                concept_type = Concept.objects.get(identifier=result.concept_type)
            except Concept.DoesNotExist:
                try:
                    concept_type_result = authority.manager.type(identifier=result.concept_type)
                except:
                    concept_type_result = None

                defaults = {
                    'added_by': user,
                    'authority': authority,
                    'authority': authority
                }
                if concept_type_result:
                    defaults.update({
                        'name': concept_type_result['name'],
                        'local_identifier': result.concept_type,
                        'description': concept_type_result['description'],

                    })
                else:
                    defaults.update({
                        'name': result.concept_type,
                        'local_identifier': result.concept_type,
                    })
                if defaults.get('name') is None:
                    defaults['name'] = result.concept_type
                concept_type = Concept.objects.create(identifier=result.concept_type, **defaults)
        else:
            concept_type = None

        concept, _ = Concept.objects.get_or_create(
            identifier=result.identifier,
            defaults={
                'added_by': user,
                'name': result.name,
                'local_identifier': result.local_identifier,
                'description': result.description,
                'concept_type': concept_type,
                'authority': authority
            }
        )

        if identities:
            _defaults = {
                'added_by': user
            }
            alt_concepts = [
                Concept.objects.get_or_create(
                    identifier=ident,
                    defaults=_defaults)[0]
                for ident in identities
            ]
            identity = Identity.objects.create(
                name = result.name,
                part_of = authority.builtin_identity_system,
                added_by = user
            )
            identity.concepts.add(concept, *alt_concepts)

        concepts.append(concept.id)
    return concepts, result_id


@app.task(name='goat.tasks.register_results', bind=True)
def register_results(self, results):
    """
    Callback for :func:`.search`\. Updates the :class:`.SearchResultSet` with
    :class:`.Concept`\s, and flags it as successful.

    Parameters
    ----------
    results : list
        Each item should be a return value (tuple) from :func:`.search`\.
    """
    print '::register_results::', results
    if not results:
        return

    result_set = None
    for concepts, result_id in results:
        if not result_set:
            result_set = SearchResultSet.objects.get(pk=result_id)
        result_set.results.add(*Concept.objects.filter(pk__in=concepts))
    result_set.state = SearchResultSet.SUCCESS
    result_set.save()
