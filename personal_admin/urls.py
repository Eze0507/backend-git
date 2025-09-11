# personal_admin/urls.py
from django.urls import path
from . import views

app_name = 'personal_admin'

urlpatterns = [
    path('roles/', views.RoleListView.as_view(), name='role-list'),
    path('roles/crear/', views.RoleCreateView.as_view(), name='role-create'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role-detail'),
    path('roles/<int:pk>/editar/', views.RoleUpdateView.as_view(), name='role-edit'),
    path('roles/<int:pk>/eliminar/', views.RoleDeleteView.as_view(), name='role-delete'),
]
