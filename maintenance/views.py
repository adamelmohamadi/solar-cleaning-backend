from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from datetime import date, timedelta
from .models import Nettoyage, Historique
from .serializers import NettoyageSerializer, HistoriqueSerializer
from users.models import User
from django.utils import timezone




class EstMainteneur(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_superuser or
            request.user.role == User.Role.MAINTENEUR
        )


class NettoyageViewSet(viewsets.ModelViewSet):
    queryset = Nettoyage.objects.all().select_related('projet')
    serializer_class = NettoyageSerializer
    permission_classes = [IsAuthenticated]

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
from django.utils import timezone

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

        # Empêcher de marquer "Terminé" sans signature
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