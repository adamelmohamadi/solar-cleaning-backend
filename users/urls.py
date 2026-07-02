from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import UserViewSet, MoiAPIView, CreerMainteneurAPIView, ChangerMotDePasseAPIView

router = DefaultRouter()
router.register(r'utilisateurs', UserViewSet, basename='utilisateurs')

urlpatterns = [
    path('utilisateurs/creer-mainteneur/', CreerMainteneurAPIView.as_view(), name='creer-mainteneur'),
    path('moi/', MoiAPIView.as_view(), name='moi'),
    path('moi/changer-mot-de-passe/', ChangerMotDePasseAPIView.as_view(), name='changer-mot-de-passe'),
] + router.urls