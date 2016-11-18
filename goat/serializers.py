from rest_framework import serializers

from goat.models import *

import json


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email')


class IdentitySystemSerializer(serializers.ModelSerializer):
    added_by = UserSerializer()

    class Meta:
        model = IdentitySystem
        fields = '__all__'


class IdentitySystemLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentitySystem
        fields = ('id', 'name')


class AuthorityLightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Authority
        fields = ('id', 'name',)


class AuthoritySerializer(serializers.ModelSerializer):
    """
    Identical to :class:`.AuthorityDetailSerializer` except that the
    configuration is hidden.
    """
    added_by = UserSerializer()
    builtin_identity_system = IdentitySystemLightSerializer()

    class Meta:
        model = Authority
        exclude = ('configuration',)


class AuthorityDetailSerializer(serializers.ModelSerializer):
    added_by = UserSerializer()
    builtin_identity_system = IdentitySystemLightSerializer()

    class Meta:
        model = Authority
        fields = '__all__'

    def validate_configuration(self, value):
        """
        If a configuration is provided, ensure that it is valid JSON.
        """
        if not value:
            try:
                json.loads(value)
            except ValueError:
                raise serializers.ValidationError("Configuration must be valid"
                                                  "JSON.")
        return value


class ConceptSerializer(serializers.ModelSerializer):
    added_by = UserSerializer()
    authority = AuthorityLightSerializer()

    class Meta:
        model = Concept
        exclude = ('data', )


class IdentitySerializer(serializers.ModelSerializer):
    added_by = UserSerializer()
    part_of = IdentitySystemLightSerializer()

    class Meta:
        model = Identity
        fields = '__all__'

    def to_internal_value(self, data):
        """
        Concepts can be passed as IDs, or as URIs.
        """
        print data
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

    def to_representation(self, obj):
        """
        Concepts should be represented as URIs.
        """
        concepts = obj.concepts.values_list('identifier', flat=True)
        data = super(IdentitySerializer, self).to_representation(obj)
        data['concepts'] = concepts
        return data
