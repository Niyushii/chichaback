from django.db import models
from core.models import Estado
from apps.tiendas.models import Tienda
from apps.categorias.models import Categoria

class Talla(models.Model):
    nombre = models.CharField(max_length=50)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='tallas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'talla'
        verbose_name = 'Talla'
        verbose_name_plural = 'Tallas'
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
        blank=True,
        null=True
    )
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='productos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'producto'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['categoria']),
        ]
    
    def __str__(self):
        return self.nombre


class TiendaProducto(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name='productos')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes_tienda')
    talla = models.ForeignKey(
        Talla,
        on_delete=models.PROTECT,
        related_name='productos_tienda',
        blank=True,
        null=True
    )
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=0)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='tienda_productos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tienda_producto'
        verbose_name = 'Producto de Tienda'
        verbose_name_plural = 'Productos de Tienda'
        unique_together = [['tienda', 'producto', 'talla']]
        indexes = [
            models.Index(fields=['tienda', 'producto']),
            models.Index(fields=['producto']),
        ]
    
    def __str__(self):
        talla_info = f" - Talla: {self.talla.nombre}" if self.talla else ""
        return f"{self.producto.nombre} en {self.tienda.nombre}{talla_info}"


class ImagenProducto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    producto = models.ForeignKey(
        TiendaProducto,
        on_delete=models.CASCADE,
        related_name='imagenes'
    )
    archivo = models.URLField(max_length=500)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='imagenes_producto')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'imagen_producto'
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Producto'
        indexes = [
            models.Index(fields=['producto']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.producto.producto.nombre}"