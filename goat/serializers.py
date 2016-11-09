from rest_framework import serializers

from goat.models import *


class AuthoritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Authority
        fields = '__all__'


class ConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Concept
        fields = '__all__'


class IdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = '__all__'


class IdentitySystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentitySystem
        fields = '__all__'
