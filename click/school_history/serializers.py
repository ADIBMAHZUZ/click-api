from rest_framework import serializers

from click.school_history.models import SchoolHistory

class SchoolHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolHistory
        fields = ('id', 'title', 'created_by', 'updated_by', 'content', 'photo', 'is_active', 'publish_date')
        read_only_fields = ('id',)

    def get_extra_kwargs(self):
        extra_kwargs = super(SchoolHistorySerializer, self).get_extra_kwargs()

        if self.instance is not None:
            kwargs = extra_kwargs.get('created_by', {})
            kwargs['read_only'] = True
            extra_kwargs['created_by'] = kwargs
        
        return extra_kwargs