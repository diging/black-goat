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
    added_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = IdentitySystem
        fields = ('id', 'name', 'added_by')


class AuthorityLightSerializer(serializers.ModelSerializer):
    added_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Authority
        fields = ('id', 'name', 'added_by')


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


class ConceptTypeSerializer(serializer.ModelSerializer):
    class Meta:
        model = Concept
        fields = ('identifier', 'name', 'description', 'id')


class ConceptSerializer(serializers.ModelSerializer):
    added_by = UserSerializer()
    authority = AuthorityLightSerializer()
    concept_type = ConceptTypeSerializer()

    class Meta:
        model = Concept
        exclude = ('data', )


class ConceptLightSerializer(serializers.ModelSerializer):
    # added_by = UserSerializer()
    # authority = AuthorityLightSerializer()
    authority = serializers.PrimaryKeyRelatedField(queryset=Authority.objects.all(), allow_null=True)
    concept_type = serializers.PrimaryKeyRelatedField(queryset=Concept.objects.all(), allow_null=True)


    class Meta:
        model = Concept
        exclude = ('data', )


class ConceptRepresentationMixin(serializers.ModelSerializer):
    concepts = serializers.PrimaryKeyRelatedField(queryset=Concept.objects.all(), many=True)

    class Meta:
        model = Identity
        fields = '__all__'

    def to_internal_value(self, data):
        """
        Concepts can be passed as IDs, or as URIs.
        """
        concepts = []
        for concept in data.getlist('concepts', []):
            if type(concept) in [str, unicode] and concept.startswith('http'):
                try:
                    concepts.append(Concept.objects.get(identifier=concept).id)
                except Concept.DoesNotExist:
                    raise serializers.ValidationError({
                        'concepts': 'No such concept: %s' % concept
                    })
            else:
                concepts.append(concept)

        data.setlist('concepts', concepts)

        return super(ConceptRepresentationMixin, self).to_internal_value(data)

    def to_representation(self, obj):
        """
        Concepts should be represented as URIs.
        """
        concepts = obj.concepts.values_list('identifier', flat=True)
        data = super(ConceptRepresentationMixin, self).to_representation(obj)
        data['concepts'] = concepts
        return data


class IdentityLightSerializer(ConceptRepresentationMixin, serializers.ModelSerializer):
    part_of = serializers.PrimaryKeyRelatedField(queryset=IdentitySystem.objects.all())
    concepts = serializers.PrimaryKeyRelatedField(queryset=Concept.objects.all(), many=True)

    class Meta:
        model = Identity
        fields = '__all__'


class IdentitySerializer(ConceptRepresentationMixin, serializers.ModelSerializer):
    added_by = UserSerializer()
    part_of = IdentitySystemLightSerializer()

    class Meta:
        model = Identity
        fields = '__all__'
