from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, GroupAuxViewSet, UserRegistrationView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'groupsAux', GroupAuxViewSet, basename='groupAux')
urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
]