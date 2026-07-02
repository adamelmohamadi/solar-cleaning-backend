from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer, CreerMainteneurSerializer


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