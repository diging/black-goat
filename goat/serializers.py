from rest_framework import serializers

from goat.models import *


class AuthoritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Authority
        fields = '__all__'

    def validate_configuration(self, value):
        """
        If a configuration is provided, ensure that it is valid JSON.
        """
        import json
        if value:
            try:
                json.loads(value)
            except ValueError:
                raise serializers.ValidationError("Configuration must be valid"
                                                  "JSON.")
        return value


class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = '__all__'


class IdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = '__all__'

    def to_internal_value(self, data):
        """
        Concepts can be passed as IDs, or as URIs.
        """
        concepts = []
        for concept in data.get('concepts', []):
            if type(concept) in [str, unicode] and concept.startswith('http'):
                try:
                    concepts.append(Concept.objects.get(identifier=concept).id)
                except Concept.DoesNotExist:
                    raise serializers.ValidationError({
                        'concepts': 'No such concept: %s' % concept
                    })
            else:
                concepts.append(concept)
        data['concepts'] = concepts
        return super(IdentitySerializer, self).to_internal_value(data)


class IdentitySystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentitySystem
        fields = '__all__'
