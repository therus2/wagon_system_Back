from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StationConfigViewSet, WagonTypeViewSet, CargoTypeViewSet,
    CisternTypeViewSet, ConductorViewSet, FirmViewSet, WagonViewSet,
    BulkWagonCreateView, ComposeView, ComposeSaveView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer


class UserInfoView(APIView):
    """Получение информации о текущем пользователе"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


router = DefaultRouter()
router.register(r'station-config', StationConfigViewSet, basename='station-config')
router.register(r'wagon-types', WagonTypeViewSet, basename='wagon-type')
router.register(r'cargo-types', CargoTypeViewSet, basename='cargo-type')
router.register(r'cistern-types', CisternTypeViewSet, basename='cistern-type')
router.register(r'conductors', ConductorViewSet, basename='conductor')
router.register(r'firms', FirmViewSet, basename='firm')
router.register(r'wagons', WagonViewSet, basename='wagon')

urlpatterns = [
    path('auth/me/', UserInfoView.as_view(), name='user-info'),
    path('wagons/bulk/', BulkWagonCreateView.as_view(), name='bulk-wagon-create'),
    path('compose/', ComposeView.as_view(), name='compose'),
    path('compose/save/', ComposeSaveView.as_view(), name='compose-save'),
    path('', include(router.urls)),
]
