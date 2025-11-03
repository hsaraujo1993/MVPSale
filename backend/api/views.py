from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema
from .serializers import HealthSerializer


class HealthView(GenericAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = HealthSerializer

    @extend_schema(summary="Health check", tags=["system"], responses={200: HealthSerializer}) 
    def get(self, request):
        serializer = self.get_serializer({"status": "ok"})
        return Response(serializer.data)
