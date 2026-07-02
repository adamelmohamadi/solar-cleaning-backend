from rest_framework import viewsets, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, timedelta
from .models import Projet
from .serializers import ProjetSerializer
from maintenance.models import Nettoyage


class ProjetViewSet(viewsets.ModelViewSet):
    queryset = Projet.objects.all()
    serializer_class = ProjetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom', 'localisation']


class GenererPlanningAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            projet = Projet.objects.get(pk=pk)
        except Projet.DoesNotExist:
            return Response({"detail": "Projet introuvable."}, status=status.HTTP_404_NOT_FOUND)

        frequence = projet.frequence_nettoyage
        if not frequence or frequence <= 0:
            return Response({"detail": "Fréquence de nettoyage invalide."}, status=status.HTTP_400_BAD_REQUEST)

        aujourd_hui = date.today()
        fin_annee = date(aujourd_hui.year, 12, 31)

        # Supprimer les nettoyages planifiés futurs existants pour éviter les doublons
        Nettoyage.objects.filter(
            projet=projet,
            statut=Nettoyage.Statut.PLANIFIE,
            date_prevue__gte=aujourd_hui
        ).delete()

        nettoyages_crees = []
        date_courante = aujourd_hui

        while date_courante <= fin_annee:
            nettoyage = Nettoyage.objects.create(
                projet=projet,
                date_prevue=date_courante,
                statut=Nettoyage.Statut.PLANIFIE,
            )
            nettoyages_crees.append(str(date_courante))
            date_courante += timedelta(days=frequence)

        return Response({
            "detail": f"{len(nettoyages_crees)} nettoyages générés pour {projet.nom}.",
            "projet": projet.nom,
            "frequence": frequence,
            "nettoyages": nettoyages_crees,
        }, status=status.HTTP_201_CREATED)