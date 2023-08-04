from rest_framework import serializers

from click.master_data.models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'name_malay', 'description', 'is_active']


    