from goat.models import *
from goat.serializers import *

from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, DjangoObjectPermissions, DjangoModelPermissions

from guardian.shortcuts import get_user_perms


def home(request):
    return

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
    permission_classes = [IsAuthenticatedOrReadOnly, DjangoObjectPermissions, DjangoModelPermissions]
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer


class AuthorityViewSet(CreateWithUserInfoMixin, viewsets.ModelViewSet):
    permission_classes = [DjangoObjectPermissions, DjangoModelPermissions]
    queryset = Authority.objects.all()
    serializer_class = AuthoritySerializer


class IdentityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
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
        print identity_system, added_by, get_user_perms(added_by, identity_system)
        if not added_by.has_perm('change_identitysystem', identity_system):
            _data = {
                'detail': "You lack authorization to add identity relations to"
                          " that identity system"
              }
            return Response(_data, status=status.HTTP_401_UNAUTHORIZED)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class IdentitySystemViewSet(CreateWithUserInfoMixin, viewsets.ModelViewSet):
    permission_classes = [DjangoObjectPermissions, DjangoModelPermissions]
    queryset = IdentitySystem.objects.all()
    serializer_class = IdentitySystemSerializer
