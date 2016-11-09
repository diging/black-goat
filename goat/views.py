from goat.models import *
from goat.serializers import *

from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, DjangoObjectPermissions, DjangoModelPermissions

from guardian.shortcuts import get_user_perms

from django.template import RequestContext, loader
from django.http import (JsonResponse, HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect, Http404, HttpResponseForbidden)


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


class CreateWithUserInfoMixin(object):
    """
    Extends the default :meth:`.ModelViewSet.create` to populate the
    ``added_by`` field.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        added_by_id = request.user.id
        serializer.initial_data['added_by'] = added_by_id
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ConceptViewSet(CreateWithUserInfoMixin, viewsets.ModelViewSet):
    permission_classes = [GoatPermission,]

    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer


class AuthorityViewSet(CreateWithUserInfoMixin, viewsets.ModelViewSet):
    permission_classes = [GoatPermission]
    queryset = Authority.objects.all()
    serializer_class = AuthoritySerializer


class IdentityViewSet(viewsets.ModelViewSet):
    permission_classes = [GoatPermission]
    queryset = Identity.objects.all()
    serializer_class = IdentitySerializer

    def create(self, request, *args, **kwargs):
        """
        Populates the ``added_by`` field with the current user, and checks that
        the user has ``change`` authorization on the :class:`.IdentitySystem`\.
        """
        serializer = self.get_serializer(data=request.data)

        if request.auth:
            added_by = request.auth.application.user.id
        else:
            added_by = request.user
        serializer.initial_data['added_by'] = added_by.id
        serializer.is_valid(raise_exception=True)
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
