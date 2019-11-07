from django.db.models import Q, Count

import django_filters

from goat.models import *


class ConceptFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='lookup_name_in_parts')
    search = django_filters.CharFilter('search_sets__task_id')
    concept_type = django_filters.ModelChoiceFilter(queryset=Concept.objects.filter(instances__isnull=False))

    def lookup_name_in_parts(self, queryset, value):
        q = Q()
        for part in value.split():
            q &= Q(name__icontains=part)
        return queryset.filter(q)

    class Meta:
        model = Concept
        fields = ['name', 'identifier', 'concept_type', 'added_by', 'authority']
        order_by = (
            ('name', 'Name (ascending)'),
            ('-name', 'Name (descending)'),
            ('concept_type', 'Type (ascending)'),
            ('-concept_type', 'Type (descending)'),
        )
