from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import date, timedelta
from django.utils import timezone
from .models import Nettoyage, Historique, AvisClient
from .serializers import NettoyageSerializer, HistoriqueSerializer, AvisClientSerializer
from users.models import User
from projects.models import Projet


class EstMainteneur(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_superuser or
            request.user.role == User.Role.MAINTENEUR
        )


class NettoyageViewSet(viewsets.ModelViewSet):
    serializer_class = NettoyageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['projet__nom', 'commentaire', 'statut']

    def get_queryset(self):
        queryset = Nettoyage.objects.all().select_related('projet')
        projet_id = self.request.query_params.get('projet')
        if projet_id:
            queryset = queryset.filter(projet__id=projet_id)
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EstMainteneur()]
        return [IsAuthenticated()]


class HistoriqueViewSet(viewsets.ModelViewSet):
    queryset = Historique.objects.all()
    serializer_class = HistoriqueSerializer
    permission_classes = [IsAuthenticated]


class NettoyageStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        dans_7_jours = today + timedelta(days=7)
        total = Nettoyage.objects.count()
        termines = Nettoyage.objects.filter(statut=Nettoyage.Statut.TERMINE).count()
        en_retard = Nettoyage.objects.filter(statut=Nettoyage.Statut.EN_RETARD).count()
        a_venir = Nettoyage.objects.filter(
            date_prevue__gte=today,
            date_prevue__lte=dans_7_jours
        ).exclude(statut=Nettoyage.Statut.TERMINE).count()
        alertes = Nettoyage.objects.filter(
            statut__in=[Nettoyage.Statut.EN_RETARD, Nettoyage.Statut.PLANIFIE],
            date_prevue__lte=dans_7_jours
        ).select_related('projet').order_by('date_prevue')[:10]
        return Response({
            "kpis": {
                "total": total,
                "termines": termines,
                "en_retard": en_retard,
                "a_venir": a_venir,
            },
            "alertes": NettoyageSerializer(alertes, many=True).data,
        })


class ModifierNettoyageMainteneurAPIView(APIView):
    permission_classes = [EstMainteneur]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, pk):
        try:
            nettoyage = Nettoyage.objects.get(pk=pk)
        except Nettoyage.DoesNotExist:
            return Response({"detail": "Nettoyage introuvable."}, status=status.HTTP_404_NOT_FOUND)

        data = {}
        if 'commentaire' in request.data:
            data['commentaire'] = request.data['commentaire']
        if 'statut' in request.data:
            data['statut'] = request.data['statut']
        if 'date_realisee' in request.data:
            data['date_realisee'] = request.data['date_realisee']
        if 'photo' in request.FILES:
            data['photo'] = request.FILES['photo']
        if 'signature' in request.FILES:
            data['signature'] = request.FILES['signature']
            data['date_signature'] = timezone.now()

        if data.get('statut') == 'TERMINE' and not nettoyage.signature and 'signature' not in request.FILES:
            return Response(
                {"detail": "Une signature est requise pour terminer un nettoyage."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = NettoyageSerializer(nettoyage, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            Historique.objects.create(
                projet=nettoyage.projet,
                utilisateur=request.user,
                action=f"Nettoyage mis à jour — statut : {data.get('statut', nettoyage.statut)}"
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MonInstallationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'CLIENT':
            return Response({"detail": "Accès refusé."}, status=403)

        projets = Projet.objects.filter(client=request.user)
        data = []

        for projet in projets:
            nettoyages = Nettoyage.objects.filter(projet=projet).order_by('date_prevue')
            prochain = nettoyages.filter(
                statut='PLANIFIE',
                date_prevue__gte=date.today()
            ).first()
            termines = nettoyages.filter(statut='TERMINE')

            data.append({
                'projet': {
                    'id': projet.id,
                    'nom': projet.nom,
                    'localisation': projet.localisation,
                    'nombre_panneaux': projet.nombre_panneaux,
                },
                'prochain_nettoyage': str(prochain.date_prevue) if prochain else None,
                'nettoyages_termines': NettoyageSerializer(termines, many=True).data,
                'total': nettoyages.count(),
                'termines_count': termines.count(),
                'taux': round((termines.count() / nettoyages.count()) * 100) if nettoyages.count() else 0,
            })

        return Response(data)


class AvisClientAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nettoyage_id):
        if request.user.role != 'CLIENT':
            return Response({"detail": "Accès refusé."}, status=403)

        try:
            nettoyage = Nettoyage.objects.get(pk=nettoyage_id, statut='TERMINE')
        except Nettoyage.DoesNotExist:
            return Response({"detail": "Nettoyage introuvable ou non terminé."}, status=404)

        avis, created = AvisClient.objects.get_or_create(
            nettoyage=nettoyage,
            client=request.user
        )
        avis.satisfaction = request.data.get('satisfaction', avis.satisfaction)
        avis.commentaire = request.data.get('commentaire', avis.commentaire)
        avis.confirme = request.data.get('confirme', avis.confirme)
        avis.save()

        return Response(AvisClientSerializer(avis).data)


class AvisAdminAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        estAdmin = request.user.is_superuser or request.user.role == 'DIRECTEUR_GENERAL'
        if not estAdmin:
            return Response({"detail": "Accès refusé."}, status=403)

        avis = AvisClient.objects.all().select_related('nettoyage', 'client', 'nettoyage__projet')
        data = [{
            'id': a.id,
            'client': a.client.username,
            'projet': a.nettoyage.projet.nom,
            'date_nettoyage': str(a.nettoyage.date_prevue),
            'satisfaction': a.satisfaction,
            'commentaire': a.commentaire,
            'confirme': a.confirme,
            'date_avis': str(a.date_avis),
        } for a in avis]

        return Response(data)