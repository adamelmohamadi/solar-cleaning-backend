from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import NettoyageViewSet, HistoriqueViewSet, NettoyageStatsAPIView, ModifierNettoyageMainteneurAPIView, MonInstallationAPIView, AvisClientAPIView, AvisAdminAPIView
from .views_rapports import RapportsAPIView

router = DefaultRouter()
router.register(r'cleanings', NettoyageViewSet, basename='cleanings')
router.register(r'history', HistoriqueViewSet, basename='history')

urlpatterns = router.urls + [
    path('rapports/', RapportsAPIView.as_view(), name='rapports'),
    path('cleanings-stats/', NettoyageStatsAPIView.as_view(), name='cleanings-stats'),
    path('cleanings/<int:pk>/mainteneur/', ModifierNettoyageMainteneurAPIView.as_view(), name='cleaning-mainteneur'),
    path('mon-installation/', MonInstallationAPIView.as_view()),
    path('nettoyages/<int:nettoyage_id>/avis/', AvisClientAPIView.as_view()),
    path('avis-admin/', AvisAdminAPIView.as_view()),
]