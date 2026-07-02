from datetime import date, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from maintenance.models import Nettoyage

class NotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        dans_7_jours = today + timedelta(days=7)
        notifications = []

        en_retard = Nettoyage.objects.filter(
            date_prevue__lt=today,
            statut__in=[Nettoyage.Statut.PLANIFIE, Nettoyage.Statut.EN_COURS]
        ).select_related('projet').order_by('date_prevue')

        for n in en_retard:
            notifications.append({
                "id": f"retard-{n.id}",
                "type": "retard",
                "projet": n.projet.nom if n.projet else "—",
                "message": f"Nettoyage en retard — prévu le {n.date_prevue.strftime('%d/%m/%Y')}",
                "date": n.date_prevue.strftime("%d/%m/%Y"),
            })

        a_venir = Nettoyage.objects.filter(
            date_prevue__gte=today,
            date_prevue__lte=dans_7_jours,
            statut=Nettoyage.Statut.PLANIFIE
        ).select_related('projet').order_by('date_prevue')

        for n in a_venir:
            notifications.append({
                "id": f"avenir-{n.id}",
                "type": "a_venir",
                "projet": n.projet.nom if n.projet else "—",
                "message": f"Nettoyage prévu le {n.date_prevue.strftime('%d/%m/%Y')}",
                "date": n.date_prevue.strftime("%d/%m/%Y"),
            })

        termines = Nettoyage.objects.filter(
            statut=Nettoyage.Statut.TERMINE,
            date_realisee__gte=today - timedelta(days=7)
        ).select_related('projet').order_by('-date_realisee')

        for n in termines:
            notifications.append({
                "id": f"termine-{n.id}",
                "type": "termine",
                "projet": n.projet.nom if n.projet else "—",
                "message": f"Nettoyage terminé le {n.date_realisee.strftime('%d/%m/%Y')}",
                "date": n.date_realisee.strftime("%d/%m/%Y"),
            })

        return Response({
            "total": len(notifications),
            "en_retard": len(en_retard),
            "a_venir": len(a_venir),
            "termines": len(termines),
            "notifications": notifications,
        })