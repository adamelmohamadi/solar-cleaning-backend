from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from projects.models import Projet
from projects.serializers import ProjetSerializer
from maintenance.models import Nettoyage, Historique
from maintenance.serializers import NettoyageSerializer, HistoriqueSerializer

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_projects = Projet.objects.count()
        total_nettoyages = Nettoyage.objects.count()
        completed = Nettoyage.objects.filter(statut=Nettoyage.Statut.TERMINE).count()
        delayed = Nettoyage.objects.filter(statut=Nettoyage.Statut.EN_RETARD).count()
        in_progress = Nettoyage.objects.filter(statut=Nettoyage.Statut.EN_COURS).count()
        planned = Nettoyage.objects.filter(statut=Nettoyage.Statut.PLANIFIE).count()
        taux_avancement = round((completed / total_nettoyages) * 100, 1) if total_nettoyages else 0
        projets_en_retard = Projet.objects.filter(
            nettoyages__statut=Nettoyage.Statut.EN_RETARD
        ).distinct().count()
        prochains_nettoyages = Nettoyage.objects.filter(
            date_prevue__gte=date.today()
        ).exclude(statut=Nettoyage.Statut.TERMINE).order_by("date_prevue")[:5]
        nettoyages_en_retard = Nettoyage.objects.filter(
            statut=Nettoyage.Statut.EN_RETARD
        ).order_by("date_prevue")[:5]
        projets_recents = Projet.objects.order_by("-date_creation")[:5]
        activite_recente = Historique.objects.order_by("-date_action")[:5]

        return Response({
            "kpis": {
                "total_projects": total_projects,
                "completed": completed,
                "in_progress": in_progress,
                "planned": planned,
                "delayed": delayed,
                "projets_en_retard": projets_en_retard,
                "taux_avancement": taux_avancement,
            },
            "prochains_nettoyages": NettoyageSerializer(prochains_nettoyages, many=True).data,
            "nettoyages_en_retard": NettoyageSerializer(nettoyages_en_retard, many=True).data,
            "projets_recents": ProjetSerializer(projets_recents, many=True).data,
            "activite_recente": HistoriqueSerializer(activite_recente, many=True).data,
        })