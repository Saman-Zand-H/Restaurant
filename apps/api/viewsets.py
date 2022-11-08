from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from .serializers import UserAddressSerializer
from delivery.models import UserAddressInfo


class UserAddressesViewset(viewsets.ModelViewSet):
    queryset = UserAddressInfo.objects.all()
    serializer_class = UserAddressSerializer
