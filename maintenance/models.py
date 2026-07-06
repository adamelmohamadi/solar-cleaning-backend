from django.db import models
from projects.models import Projet
from django.conf import settings


class Nettoyage(models.Model):

    class Statut(models.TextChoices):
        PLANIFIE = "PLANIFIE", "Planifié"
        EN_COURS = "EN_COURS", "En cours"
        TERMINE = "TERMINE", "Terminé"
        EN_RETARD = "EN_RETARD", "En retard"

    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='nettoyages'
    )

    date_prevue = models.DateField()

    date_realisee = models.DateField(
        null=True,
        blank=True
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.PLANIFIE
    )

    commentaire = models.TextField(
        blank=True
    )

    photo = models.ImageField(
        upload_to='nettoyages/',
        blank=True,
        null=True
    )

    signature = models.ImageField(
        upload_to='signatures/',
        blank=True,
        null=True
    )

    date_signature = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.projet.nom} - {self.date_prevue}"
    
class Historique(models.Model):

    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE
    )

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    action = models.CharField(
        max_length=255
    )

    date_action = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.action
    
class AvisClient(models.Model):
    class Satisfaction(models.TextChoices):
        SATISFAIT = 'SATISFAIT', 'Satisfait'
        NEUTRE = 'NEUTRE', 'Neutre'
        INSATISFAIT = 'INSATISFAIT', 'Insatisfait'

    nettoyage = models.OneToOneField(
        Nettoyage,
        on_delete=models.CASCADE,
        related_name='avis_client'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='avis'
    )
    satisfaction = models.CharField(
        max_length=20,
        choices=Satisfaction.choices
    )
    commentaire = models.TextField(blank=True)
    confirme = models.BooleanField(default=False)
    date_avis = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"avis {self.client.username}-{self.nettoyage}"