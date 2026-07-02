from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from projects.models import Projet
from maintenance.models import Nettoyage, Historique


class RapportsAPIView(APIView):
    def get(self, request):
        total_nettoyages = Nettoyage.objects.count()
        termines = Nettoyage.objects.filter(statut=Nettoyage.Statut.TERMINE).count()
        en_retard = Nettoyage.objects.filter(statut=Nettoyage.Statut.EN_RETARD).count()
        taux_avancement = round((termines / total_nettoyages) * 100, 1) if total_nettoyages else 0

        mois_actuel = date.today().month
        annee_actuelle = date.today().year
        ce_mois = Nettoyage.objects.filter(
            date_realisee__month=mois_actuel,
            date_realisee__year=annee_actuelle,
            statut=Nettoyage.Statut.TERMINE
        ).count()

        historique = Nettoyage.objects.filter(
            statut=Nettoyage.Statut.TERMINE
        ).select_related('projet').order_by('-date_realisee')

        historique_data = [
            {
                "id": n.id,
                "projet": n.projet.nom if n.projet else "—",
                "date_prevue": n.date_prevue.strftime("%d/%m/%Y") if n.date_prevue else "—",
                "date_realisee": n.date_realisee.strftime("%d/%m/%Y") if n.date_realisee else "—",
                "commentaire": n.commentaire or "—",
            }
            for n in historique
        ]

        retards = Nettoyage.objects.filter(
            statut=Nettoyage.Statut.EN_RETARD
        ).select_related('projet').order_by('date_prevue')

        retards_data = [
            {
                "id": n.id,
                "projet": n.projet.nom if n.projet else "—",
                "date_prevue": n.date_prevue.strftime("%d/%m/%Y") if n.date_prevue else "—",
                "commentaire": n.commentaire or "—",
            }
            for n in retards
        ]

        projets = Projet.objects.prefetch_related('nettoyages').all()
        avancement_projets = []
        for p in projets:
            total = p.nettoyages.count()
            done = p.nettoyages.filter(statut=Nettoyage.Statut.TERMINE).count()
            taux = round((done / total) * 100) if total else 0
            avancement_projets.append({
                "id": p.id,
                "nom": p.nom,
                "localisation": p.localisation,
                "total": total,
                "termines": done,
                "taux": taux,
            })

        return Response({
            "kpis": {
                "taux_avancement": taux_avancement,
                "termines": termines,
                "en_retard": en_retard,
                "ce_mois": ce_mois,
            },
            "historique": historique_data,
            "retards": retards_data,
            "avancement_projets": avancement_projets,
        })