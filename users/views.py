from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer, CreerMainteneurSerializer
from django.contrib.auth.hashers import make_password
import random
import string
from projects.models import Projet
from maintenance.models import AvisClient 


class EstAdminOuDG(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_superuser or
            request.user.role == User.Role.DIRECTEUR_GENERAL
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class MoiAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class CreerMainteneurAPIView(APIView):
    permission_classes = [EstAdminOuDG]

    def post(self, request):
        serializer = CreerMainteneurSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangerMotDePasseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ancien = request.data.get("ancien_mot_de_passe")
        nouveau = request.data.get("nouveau_mot_de_passe")

        if not ancien or not nouveau:
            return Response(
                {"detail": "Les deux champs sont requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(ancien):
            return Response(
                {"detail": "Ancien mot de passe incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(nouveau) < 6:
            return Response(
                {"detail": "Le nouveau mot de passe doit contenir au moins 6 caractères."},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(nouveau)
        request.user.save()
        return Response({"detail": "Mot de passe mis à jour avec succès."})
    
class ClientsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        estAdmin = request.user.is_superuser or request.user.role == 'DIRECTEUR_GENERAL'
        if not estAdmin:
            return Response({"detail": "Accès refusé."}, status=403)

        clients = User.objects.filter(role='CLIENT')
        data = []

        for client in clients:
            projets = Projet.objects.filter(client=client)
            avis = AvisClient.objects.filter(client=client).order_by('-date_avis')[:3]

            data.append({
                'id': client.id,
                'username': client.username,
                'nom': f"{client.first_name} {client.last_name}".strip() or client.username,
                'email': client.email or "—",
                'projets': [{'id': p.id, 'nom': p.nom, 'localisation': p.localisation} for p in projets],
                'avis_recents': [{
                    'satisfaction': a.satisfaction,
                    'commentaire': a.commentaire,
                    'confirme': a.confirme,
                    'date': str(a.date_avis)[:10],
                } for a in avis],
            })

        return Response(data)


class ResetPasswordClientAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        estAdmin = request.user.is_superuser or request.user.role == 'DIRECTEUR_GENERAL'
        if not estAdmin:
            return Response({"detail": "Accès refusé."}, status=403)

        try:
            client = User.objects.get(pk=pk, role='CLIENT')
        except User.DoesNotExist:
            return Response({"detail": "Client introuvable."}, status=404)

        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        client.password = make_password(new_password)
        client.save()

        return Response({
            'username': client.username,
            'password': new_password,
            'nom': f"{client.first_name} {client.last_name}".strip() or client.username,
        })