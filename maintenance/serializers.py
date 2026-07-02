from rest_framework import serializers
from .models import Nettoyage, Historique

class NettoyageSerializer(serializers.ModelSerializer):
    projet_nom = serializers.CharField(source='projet.nom', read_only=True)

    class Meta:
        model = Nettoyage
        fields = [
            'id', 'projet', 'projet_nom', 'date_prevue',
            'date_realisee', 'statut', 'commentaire', 'photo', 'signature', 'date_signature'
        ]

class HistoriqueSerializer(serializers.ModelSerializer):
    projet_nom = serializers.CharField(source='projet.nom', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True)

    class Meta:
        model = Historique
        fields = ['id', 'action', 'date_action', 'projet_nom', 'utilisateur_nom']