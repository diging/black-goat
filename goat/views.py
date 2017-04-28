from __future__ import absolute_import


from goat.models import *
from goat.serializers import *
from goat import tasks, filters

from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import detail_route, list_route, api_view, permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, DjangoObjectPermissions, DjangoModelPermissions
from django_filters.rest_framework import DjangoFilterBackend

from guardian.shortcuts import get_user_perms

from django.template import RequestContext, loader
from django.http import (JsonResponse, HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect, Http404, HttpResponseForbidden)
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from celery.result import AsyncResult

from itertools import groupby
import urllib


class IdentityIterator:
    """
    Wrapper for :class:`.QuerySet` that enforces identity-uniqueness for all
    or a set of :class:`.IdentitySystem`\s.
    """
    def __init__(self, queryset, identity_systems=None):
        self.queryset = queryset
        self.identity_systems = identity_systems
        print "identity_systems", identity_systems

    def __iter__(self):
        self.queryset = self.queryset.__iter__()
        return self

    def __len__(self):
        return self.queryset.count()

    def __getitem__(self, key):
        if isinstance(key, slice):
            self.queryset = self.queryset[key]
        return self

    def next(self):
        instance = self.queryset.next()
        if instance is None:
            raise StopIteration()

        ident_qs = instance.identities
        if ident_qs.count() == 0:
            return instance

        if self.identity_systems:
            ident_qs = ident_qs.filter(part_of__id__in=self.identity_systems.values_list('id', flat=True))

        identical_ids = ident_qs.values_list('id', flat=True)
        lead_concept = Concept.objects.filter(identities__in=identical_ids).distinct('id').order_by('id').first()
        if lead_concept is None:
            return instance

        if instance.id != lead_concept.id:
            return self.next()
        return instance


class GoatPermission(BasePermission):
    def has_permission(self, request, view):
        model_name = view.__class__.queryset.model.__name__.lower()
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method in ['PUT', 'POST', 'PATCH']:
            return request.user.has_perm('goat.add_%s' % model_name)
        elif request.method == 'DELETE':
            return False

    def has_object_permission(self, request, view, obj):
        model_name = type(obj).__name__.lower()
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method in ['PUT', 'POST', 'PATCH']:
            return request.user.has_perm('change_%s' % model_name, obj)
        elif request.method == 'DELETE':
            return request.user.has_perm('delete_%s' % model_name, obj)


def home(request):
    """
    Just a goat.
    """
    context = RequestContext(request, {})
    return HttpResponse(loader.get_template('goat/base.html').render(context))


def identical(request):
    """
    This provides a simpler view onto :class:`.Identity` instances than the
    :class:`.IdentityViewSet`\. Here the client can pass an identifier and
    (optionally) an ID for a :class:`.IdentitySystem` instance, and get an
    array of identical :class:`.Concept`\s.
    """

    concept = get_object_or_404(Concept, identifier=request.GET.get('identifier'))

    identities = concept.identities.all()

    system_id = request.GET.get('system')
    if system_id:
        identities = identities.filter(part_of_id=system_id)
    try:    # The QuerySet is lazy, so we do the serialization in here.
        concepts = Concept.objects.filter(identities__in=identities.values_list('id', flat=True)).distinct('id')
        serialized = ConceptSerializer(concepts, many=True).data
    except:    # This is kind of a drag, but SQLite doesn't support DISTINCT ON.
        concepts = Concept.objects.filter(identities__in=identities.values_list('id', flat=True))
        concepts = [[c for c in concept][0] for i, concept in groupby(sorted(concepts, key=lambda o: o.id), key=lambda o: o.id)]
        serialized = ConceptSerializer(concepts, many=True).data

    return JsonResponse({'results': serialized})


def retrieve(request):
    """
    Get a :class:`.Concept` by identifier.
    """
    identifier = request.GET.get('identifier')
    concept = get_object_or_404(Concept, identifier=identifier)
    serialized = ConceptSerializer(concept).data
    return JsonResponse(serialized)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def search(request):
    """
    Trigger a search.

    Since we may be searching quite a few authority systems, this view kicks
    off an asynchronous search strategy and forwards the client to the search
    status view.

    TODO: should be able to filter the authorities used in the search.
    """

    q = request.GET.get('q', None)
    if not q:
        return JsonResponse({'detail': 'No query provided.'}, status=400)

    params = {k: v[0] if isinstance(v, list) else v
              for k, v in dict(request.GET.copy()).iteritems()}

    # The client can coerce a new search even if we have results for an
    #  identical query.
    force = params.pop('force', None)

    if force is not None:
        # Look for an identical search in the last 24 hours,
        #  and use those results instead of re-running the entire search.
        params_serialized = urllib.urlencode(params)
        recent_search = SearchResultSet.objects.filter(parameters=params_serialized,
                                                       created__gte=timezone.now()-timedelta(hours=24)).first()
        if recent_search is not None:
            relative_path = reverse('search') + recent_search.task_id + u'/'
            return HttpResponseRedirect(relative_path)


    # We let the asynchronous task create the SearchResultSet, since it will
    #  spawn tasks that need to update the SearchResultSet upon completion.
    result = tasks.orchestrate_search.delay(request.user.id, list(Authority.objects.all().values_list('id', flat=True)),
                                            params)

    # We have to build this manually, since the SearchResultSet probably does
    #  not yet exist.
    relative_path = reverse('search') + result.id + u'/'
    return HttpResponseRedirect(relative_path)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def search_results(request, result_id):
    """
    Check the status of a search.
    """
    # It is possible for the client to end up here before the SearchResultSet
    #  is created (e.g. if Celery is super backed-up). So we'll just pretend
    #  that it exists, and placate the client with a soothing message.
    try:
        result = SearchResultSet.objects.get(task_id=result_id)
    except SearchResultSet.DoesNotExist:
        return JsonResponse({'detail': "Your search is pending creation."},
                            status=202)

    # Only the owner of the search can check its status here.
    # if result.added_by != request.user:
    #     _data, _status = {'detail': "This search does not belong to you."}, 403

    if result.state == SearchResultSet.PENDING:
        _data = {
            'detail': "Your search is being executed; please check back later."
        }
        _status = 202   # Accepted.



    # If the search was successful, send the client to the concept list view
    #  with the appropriate search filter parameter.
    elif result.state == SearchResultSet.SUCCESS:
        limit = request.GET.get('limit')
        redirect_target = reverse('concept-list') + u'?search=' + result.task_id
        if limit:
            redirect_target += '&limit=' + str(limit)
        return HttpResponseRedirect(redirect_target)
    else:    # TODO: Probably we should say something more informative here.
        _data, _status = {'detail': result.state}, 200
    return JsonResponse(_data, status=_status)


class CreateWithUserInfoMixin(object):
    """
    Extends the default :meth:`.ModelViewSet.create` to populate the
    ``added_by`` field.
    """

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        data['added_by'] = request.user.id
        data['authority'] = data.get('authority', None)
        data['concept_type'] = data.get('concept_type', None)
        print data

        serializer = self.get_serializer(data=data)
        print serializer, type(serializer)

        if not serializer.is_valid(raise_exception=False):
            return Response({'detail': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ConceptViewSet(CreateWithUserInfoMixin, viewsets.ModelViewSet):
    permission_classes = [GoatPermission,]
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    filter_backends = (DjangoFilterBackend, )
    filter_class = filters.ConceptFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return ConceptLightSerializer
        return super(ConceptViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        identitysystem_ids = request.GET.getlist('identitysystem')
        if identitysystem_ids:
            systems = IdentitySystem.objects.filter(pk__in=identitysystem_ids)
            iterator = IdentityIterator(queryset, systems)
        else:
            iterator = IdentityIterator(queryset)
        page = self.paginate_queryset(iterator)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AuthorityViewSet(CreateWithUserInfoMixin, viewsets.ModelViewSet):
    permission_classes = [GoatPermission]
    queryset = Authority.objects.all()
    serializer_class = AuthoritySerializer
    filter_backends = (DjangoFilterBackend, )

    def get_serializer_class(self):
        """
        Don't show the configuration in the list view.
        """
        if self.action == 'list':
            return AuthoritySerializer
        elif self.action == 'create':
            return AuthorityLightSerializer
        return AuthorityDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Populates the ``added_by`` field with the current user.
        """
        print '::: create'
        print request.user
        data = request.data.copy()
        added_by = request.user
        data['added_by'] = added_by.id

        serializer = self.get_serializer(data=data)

        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class IdentityViewSet(viewsets.ModelViewSet):
    permission_classes = [GoatPermission]
    queryset = Identity.objects.all()
    serializer_class = IdentitySerializer
    filter_backends = (DjangoFilterBackend, )

    def get_serializer_class(self):
        if self.action == 'create':
            return IdentityLightSerializer
        return super(IdentityViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        """
        Populates the ``added_by`` field with the current user, and checks that
        the user has ``change`` authorization on the :class:`.IdentitySystem`\.
        """
        data = request.data.copy()
        added_by = request.user
        data['added_by'] = added_by.id

        serializer = self.get_serializer(data=data)

        serializer.is_valid(raise_exception=True)
        print serializer.errors
        identity_system = serializer.validated_data.get('part_of')
        if not added_by.has_perm('change_identitysystem', identity_system):
            _data = {
                'detail': "You lack authorization to add identity relations to"
                          " that identity system."
              }
            return Response(_data, status=status.HTTP_401_UNAUTHORIZED)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class IdentitySystemViewSet(CreateWithUserInfoMixin, viewsets.ModelViewSet):
    permission_classes = [GoatPermission]
    queryset = IdentitySystem.objects.all()
    serializer_class = IdentitySystemSerializer
    filter_backends = (DjangoFilterBackend, )

    def get_serializer_class(self):
        if self.action == 'create':
            return IdentitySystemLightSerializer
        return super(IdentitySystemViewSet, self).get_serializer_class()

    def create(self, request, *args, **kwargs):
        """
        Populates the ``added_by`` field with the current user.
        """
        print '::: create'
        print request.user
        data = request.data.copy()
        added_by = request.user
        data['added_by'] = added_by.id

        serializer = self.get_serializer(data=data)

        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
