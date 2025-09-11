from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.models import Group
from .forms import GroupForm

# LISTAR
class RoleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'auth.view_group'
    model = Group
    template_name = 'personal_admin/role_list.html'
    context_object_name = 'roles'
    ordering = ['name']

# DETALLE
class RoleDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'auth.view_group'
    model = Group
    template_name = 'personal_admin/role_detail.html'
    context_object_name = 'role'

# CREAR
class RoleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'auth.add_group'
    model = Group
    form_class = GroupForm
    template_name = 'personal_admin/role_form.html'
    success_url = reverse_lazy('personal_admin:role-list')

# EDITAR
class RoleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'auth.change_group'
    model = Group
    form_class = GroupForm
    template_name = 'personal_admin/role_form.html'
    success_url = reverse_lazy('personal_admin:role-list')

# ELIMINAR
class RoleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'auth.delete_group'
    model = Group
    template_name = 'personal_admin/role_confirm_delete.html'
    success_url = reverse_lazy('personal_admin:role-list')
