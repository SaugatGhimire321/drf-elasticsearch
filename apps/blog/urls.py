from django.urls import path, include
from rest_framework import routers

from apps.blog.views import UserViewSet, CategoryViewSet, ArticleViewSet


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'articles', ArticleViewSet)

urlpatterns = [
    path("", include(router.urls))
]