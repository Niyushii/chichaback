from django.db import models
from core.models import Estado

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    icono = models.URLField(max_length=500, blank=True, null=True)
    categoria_padre = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subcategorias'
    )
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='categorias')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categoria'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        indexes = [
            models.Index(fields=['categoria_padre']),
        ]
    
    def __str__(self):
        if self.categoria_padre:
            return f"{self.categoria_padre.nombre} > {self.nombre}"
        return self.nombre