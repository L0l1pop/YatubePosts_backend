from rest_framework import serializers, status
from rest_framework.relations import SlugRelatedField, StringRelatedField
import base64
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from  rest_framework.exceptions import APIException

from posts.models import Comment, Post, Group, Follow, User

class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')  
            ext = format.split('/')[-1]  
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
    
class ConflictError(APIException):
    status_code = 409
    default_detail = 'Conflict'
    default_code = 'conflict'

class PostSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True, default = serializers.CurrentUserDefault())
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        fields = ('id', 'author', 'text', 'pub_date', 'image', 'group')
        read_only_fields = ('author', 'pub_date')
        model = Post

    def create(self, validated_data):
        group = validated_data.pop('group', None)
        post = Post.objects.create(**validated_data)
        if group is not None:
            current_group = get_object_or_404(Group, pk=group.id)
            post.group = current_group
        else:
            post.group = None
        post.save()
        return post
    
class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ('id', 'title', 'slug', 'description')


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username', default=serializers.CurrentUserDefault()
    )

    class Meta:
        fields = ('id', 'author', 'text', 'created', 'post')
        read_only_fields = ('author', 'created', 'post')
        model = Comment


class FollowSerializer(serializers.ModelSerializer):
    user = SlugRelatedField(slug_field='username', read_only=True, default = serializers.CurrentUserDefault())
    following = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()  
    )

    class Meta:
        fields = ('user', 'following')
        model = Follow

    def create(self, validated_data):
        following_user = validated_data.pop('following')
        user = validated_data.pop('user')

        if following_user == user:
            raise ConflictError('User cannot subscribe to himself')

        follow = Follow.objects.create(user=user, following=following_user)
        follow.save()
        return follow