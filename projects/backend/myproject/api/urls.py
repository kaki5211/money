# api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet

# ルーターを初期化
router = DefaultRouter()
# 'articles' というURLでArticleViewSetを登録
router.register(r'articles', ArticleViewSet)

# アプリのURLパターンを定義
urlpatterns = [
    # ルーターが生成したURLを読み込む
    path('', include(router.urls)),
]