from django.db import models
from core.models import Estado
from apps.usuarios.models import Usuario


class Tienda(models.Model):
    propietario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='tiendas')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    foto_perfil = models.URLField(max_length=500, blank=True, null=True)
    codigo_qr = models.URLField(max_length=500, blank=True, null=True)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='tiendas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tienda'
        verbose_name = 'Tienda'
        verbose_name_plural = 'Tiendas'
        indexes = [
            models.Index(fields=['propietario']),
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return f"{self.nombre} (Propietario: {self.propietario.username})"