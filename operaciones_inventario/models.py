from django.db import models

class Marca(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100,unique=True)
    logo_url = models.URLField()
    pais_origen = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

