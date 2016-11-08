from django.db import models
from django.contrib.auth.models import User


opt = {'blank': True, 'null': True}


class Authority(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(User, related_name='authorities')
    added = models.DateTimeField(auto_now_add=True)


class Concept(models.Model):
    """
    Represents a single entry in an authority service or system.

    For example, this might be an entry for a particular person in the Library
    of Congress or VIAF.
    """

    authority = models.ForeignKey('Authority', related_name='concepts')
    """The authority system to which this concept belongs."""

    name = models.CharField(max_length=255)
    """Primary name or label, used for search and display."""

    identifier = models.CharField(max_length=255)
    """The symbol used by ``authority`` to identify this concept."""

    description = models.TextField(null=True, blank=True)
    """If available, a freeform description provided by the authority."""

    added_by = models.ForeignKey(User, related_name='concepts')
    """The user who added this concept."""

    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    data = models.TextField(blank=True, null=True)
    """JSON-pickled data about this concept from the authority service."""

    concept_type = models.ForeignKey('Concept', related_name='instances', **opt)
    """
    Some authority systems may have type ontologies. Types should be treated as
    concepts.
    """
