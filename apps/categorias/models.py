from django.db import models

class Categoria(models.Model):
    categoriaID = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    icono = models.CharField(max_length=255, blank=True, null=True)
    categoriaPadre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategorias'
    )
    estado = models.CharField(
        max_length=20,
        default='activo',
    )
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    fechaEliminacion = models.DateTimeField(null=True, blank=True)
    fechaModificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categoria'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre