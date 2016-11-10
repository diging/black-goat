from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.conf import settings
from guardian.shortcuts import assign_perm

from goat.models import *


@receiver(post_save, sender=User)
def user_post_save(sender, **kwargs):
    """
    All users should be able to create by default.
    """
    user, created = kwargs.get("instance"), kwargs.get("created")
    if created and user.username != settings.ANONYMOUS_USER_NAME:
        perms = ['add_concept', 'add_authority',
                 'add_identity', 'add_identitysystem']
        for codename in perms:
            user.user_permissions.add(Permission.objects.get(codename=codename))


@receiver(post_save, sender=IdentitySystem)
def identity_system_post_save(sender, **kwargs):
    identity_system, created = kwargs.get("instance"), kwargs.get("created")
    if created:
        user = identity_system.added_by
        assign_perm("change_identitysystem", user, identity_system)
        assign_perm("delete_identitysystem", user, identity_system)
        assign_perm("add_identitysystem", user, identity_system)



@receiver(post_save, sender=Identity)
def identity_post_save(sender, **kwargs):
    identity, created = kwargs.get("instance"), kwargs.get("created")
    if created:
        user = identity.added_by
        assign_perm("change_identity", user, identity)
        assign_perm("delete_identity", user, identity)
        assign_perm("add_identity", user, identity)


@receiver(post_save, sender=Concept)
def concept_post_save(sender, **kwargs):
    concept, created = kwargs.get("instance"), kwargs.get("created")
    if created:
        user = concept.added_by
        assign_perm("change_concept", user, concept)
        assign_perm("delete_concept", user, concept)
        assign_perm("add_concept", user, concept)


@receiver(post_save, sender=Authority)
def authority_post_save(sender, **kwargs):
    authority, created = kwargs.get("instance"), kwargs.get("created")
    if created:
        user = authority.added_by
        assign_perm("change_authority", user, authority)
        assign_perm("delete_authority", user, authority)
        assign_perm("add_authority", user, authority)

        authority.builtin_identity_system = IdentitySystem.objects.create(
            name = u'builtin:%s' % authority.name,
            added_by = authority.added_by
        )
