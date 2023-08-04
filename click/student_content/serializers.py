from rest_framework import serializers


from click.student_content.models import StudentContent

class StudentContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentContent
        fields = ('id', 'title', 'content', 'photo', 'created_by', 'updated_by', 'is_active', 'status', 'publish_date')
        read_only_fields = ('id',)

    def get_extra_kwargs(self):
        extra_kwargs = super(StudentContentSerializer, self).get_extra_kwargs()

        if self.instance is not None:

            kwargs = extra_kwargs.get('created_by', {})
            kwargs['read_only'] = True
            extra_kwargs['created_by'] = kwargs
        return extra_kwargs