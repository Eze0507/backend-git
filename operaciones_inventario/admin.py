
from django.contrib import admin
from .models import Inventario

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
	list_display = ('id', 'nombre', 'codigo', 'categoria', 'tipo', 'precio', 'stock', 'fabricante')
	search_fields = ('nombre', 'codigo', 'categoria', 'tipo', 'fabricante')
	list_filter = ('categoria', 'tipo', 'fabricante')
