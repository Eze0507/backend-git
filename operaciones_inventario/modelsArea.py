# from django.db import models

from django.db import models
from personal_admin.models_saas import Tenant

class Area(models.Model):
	id = models.AutoField(primary_key=True)
	tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='areas')
	nombre = models.CharField(max_length=100)

	def __str__(self):
		return self.nombre
