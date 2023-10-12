from rest_framework import serializers

from . models import * 

class NoteSerializer(serializers.ModelSerializer):
    tags = serializers.StringRelatedField(many=True, required=False)
    shared_users = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Note
        fields = ['id' ,'title', 'content', 'tags', 'shared_users']

    def create(self, validated_data):
        created_by = self.context.get('user')
        if created_by is None:
            raise ValueError("노트 만든 이가 없음")
        
        raw_tags=validated_data.get('tags', [])
        raw_shared_users=validated_data.get('shared_users', [])
        tags = Tag.objects.filter(name__in=raw_tags)
        shared_users = User.objects.filter(pk__in=raw_shared_users)
        
        note = Note.objects.create(
            created_by=created_by,
            title=validated_data['title'],
            content=validated_data['content'],
        )

        note.tags.set(tags)
        note.shared_users.set(shared_users)
        note.shared_users.add(created_by)

        version = Version.objects.create(
            note=note,
            content=note.content,
            user=note.created_by,
            prev_version=None,
            next_version=None
        )

        return note


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class NoteShareRequestSerializer(serializers.Serializer):
    note = serializers.PrimaryKeyRelatedField(queryset=Note.objects.all())
    #shared_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_empty=True)
    shared_with = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_empty=False))


class NoteShareAcceptSerializer(serializers.Serializer):
    note = serializers.PrimaryKeyRelatedField(queryset=Note.objects.all())
    shared_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_empty=False)

    def validate(self, data):
        note_id = data['note'].id
        
        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 노트')
        
        self.instance = note
        
        return data 

    def update(self, instance, validated_data):

        user = self.context.get('user')

        self.instance.shared_users.add(user)

        return self.instance
    
class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = '__all__'

class NoteCommitSerializer(serializers.Serializer):
    current_version = serializers.PrimaryKeyRelatedField(queryset=Version.objects.all())
    new_content = serializers.CharField(allow_blank=True)

