from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article  # 対象となるモデルを指定
        fields = ['id', 'title', 'content', 'author', 'created_at'] # APIで送受信するフィールドを指定
        # fields = '__all__' と書くと全てのフィールドを対象にできます
        