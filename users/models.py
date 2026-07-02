from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        MAINTENEUR = "MAINTENEUR", "Mainteneur"
        CHEF_PROJET = "CHEF_PROJET", "Chef de Projet"
        DIRECTEUR_TECHNIQUE = "DIRECTEUR_TECHNIQUE", "Directeur Technique"
        DIRECTEUR_GENERAL = "DIRECTEUR_GENERAL", "Directeur Général"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.MAINTENEUR
    )

    def __str__(self):
        return f"{self.username} ({self.role})"