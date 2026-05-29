from rest_framework import serializers
from .models import DataPoint


class DataPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataPoint
        fields = '__all__'
        read_only_fields = ('promoted', 'pca_x', 'pca_y', 'created_at')