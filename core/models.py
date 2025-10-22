from django.db import models


class Estado(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    
    class Meta:
        db_table = 'estado'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
    
    def __str__(self):
        return self.nombre