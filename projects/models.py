from django.db import models
from django.conf import settings


class Projet(models.Model):
    nom = models.CharField(max_length=200)
    localisation = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    nombre_panneaux = models.PositiveIntegerField()
    frequence_nettoyage = models.PositiveIntegerField(help_text="Fréquence en jours")
    responsable_maintenance = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="projets"
    )
    date_creation = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nom