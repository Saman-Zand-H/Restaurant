from rest_framework import serializers
from azbankgateways.models import Bank


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        exclude = []
        