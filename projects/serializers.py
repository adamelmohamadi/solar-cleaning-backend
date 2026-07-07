from rest_framework import serializers
from .models import Projet


class ProjetSerializer(serializers.ModelSerializer):
    nom_client = serializers.CharField(write_only=True, required=False, allow_blank=True)
    client_nom = serializers.CharField(source='client.get_full_name', read_only=True)

    class Meta:
        model = Projet
        fields = [
            'id', 'nom', 'localisation', 'latitude', 'longitude',
            'nombre_panneaux', 'frequence_nettoyage', 'responsable_maintenance',
            'date_creation', 'client', 'client_nom', 'nom_client'
        ]

    def create(self, validated_data):
        validated_data.pop('nom_client', None)
        return super().create(validated_data)