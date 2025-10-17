from django.db import models
from core.models import Estado
from apps.usuarios.models import Usuario
from apps.productos.models import TiendaProducto


class Favoritos(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='favoritos')
    tienda_producto = models.ForeignKey(
        TiendaProducto,
        on_delete=models.CASCADE,
        related_name='favoritos'
    )
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='favoritos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'favoritos'
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
        unique_together = [['usuario', 'tienda_producto']]
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['tienda_producto']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.tienda_producto.producto.nombre}"