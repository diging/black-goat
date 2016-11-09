from django.db import models
from django.contrib.auth.models import User

import datetime


opt = {'blank': True, 'null': True}


class BasicAccessionMixin(models.Model):
    """
    Basic data tracking information.
    """
    class Meta:
        abstract = True

    added_by = models.ForeignKey(User)
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Authority(BasicAccessionMixin):
    """
    An Authority service, system, file, or other source of concepts.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(**opt)

    configuration = models.TextField(**opt)
    """JSON-serialized configuration (if available) for this authority."""

    def __unicode__(self):
        return self.name


class Concept(BasicAccessionMixin):
    """
    Represents a single entry in an authority service or system.

    For example, this might be an entry for a particular person in the Library
    of Congress or VIAF.
    """

    authority = models.ForeignKey('Authority', related_name='concepts')
    """The authority system to which this concept belongs."""

    name = models.CharField(max_length=255)
    """Primary name or label, used for search and display."""

    identifier = models.CharField(max_length=255, unique=True)
    """The symbol used by ``authority`` to identify this concept."""

    description = models.TextField(null=True, blank=True)
    """If available, a freeform description provided by the authority."""

    data = models.TextField(blank=True, null=True)
    """JSON-pickled data about this concept from the authority service."""

    concept_type = models.ForeignKey('Concept', related_name='instances', **opt)
    """
    Some authority systems may have type ontologies. Types should be treated as
    concepts.
    """

    def __unicode__(self):
        return self.name


class IdentitySystem(BasicAccessionMixin):
    """
    An identity system organizes a set of identity propositions about concepts.

    This allows many different identity models to coexist for different
    purposes, without having to commit to a particular view of the world.
    """

    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Identity(BasicAccessionMixin):
    """
    An identity proposition about a set of concepts.
    """

    name = models.CharField(max_length=255, **opt)
    """Can be used to provide an appellation for the cluster of concepts."""

    part_of = models.ForeignKey('IdentitySystem', related_name='identities')
    """The system to which this identity belongs."""

    confidence = models.FloatField(default=1.0)
    """This can (optionally) be used to express relative confidence levels."""

    concepts = models.ManyToManyField('Concept', related_name='identities')
    """The concepts asserted to be identical."""

    def __unicode__(self):
        return self.name
