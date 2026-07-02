from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ProjetViewSet, GenererPlanningAPIView

router = DefaultRouter()
router.register(r'projects', ProjetViewSet, basename='projects')

urlpatterns = router.urls + [
    path('projects/<int:pk>/generer-planning/', GenererPlanningAPIView.as_view(), name='generer-planning'),
]