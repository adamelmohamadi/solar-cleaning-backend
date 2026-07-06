from rest_framework import viewsets, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, timedelta
from django.utils.text import slugify
import random
import string
from .models import Projet
from .serializers import ProjetSerializer
from maintenance.models import Nettoyage
from users.models import User


class ProjetViewSet(viewsets.ModelViewSet):
    queryset = Projet.objects.all()
    serializer_class = ProjetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['nom', 'localisation']

    def create(self, request, *args, **kwargs):
        nom_client = request.data.get('nom_client', '').strip()

        client = None
        client_info = None

        if nom_client:
            base_username = slugify(nom_client).replace('-', '.')
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            parts = nom_client.split()
            client = User.objects.create_user(
                username=username,
                first_name=parts[0] if parts else nom_client,
                last_name=' '.join(parts[1:]) if len(parts) > 1 else '',
                password=password,
                role='CLIENT',
                is_active=True,
            )

            client_info = {
                'username': username,
                'password': password,
                'nom': nom_client,
            }

        data = request.data.copy()
        if client:
            data['client'] = client.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_data = serializer.data
        if client_info:
            response_data['client_info'] = client_info

        return Response(response_data, status=status.HTTP_201_CREATED)


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

        Nettoyage.objects.filter(
            projet=projet,
            statut=Nettoyage.Statut.PLANIFIE,
            date_prevue__gte=aujourd_hui
        ).delete()

        nettoyages_crees = []
        date_courante = aujourd_hui

        while date_courante <= fin_annee:
            Nettoyage.objects.create(
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