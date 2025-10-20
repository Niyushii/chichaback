from django.db import models
from core.models import Estado
from apps.usuarios.models import User
from apps.tiendas.models import Tienda
from apps.productos.models import TiendaProducto


class Venta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ventas')
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='ventas')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='ventas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'venta'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['tienda']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Venta #{self.id} - {self.usuario.username} en {self.tienda.nombre}"
    
    def calcular_total(self):
        total = sum(
            detalle.cantidad * detalle.precio_unitario 
            for detalle in self.detalles.all()
        )
        self.total = total
        return total

class VentaProducto(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    tienda_producto = models.ForeignKey(
        TiendaProducto,
        on_delete=models.PROTECT,
        related_name='ventas'
    )
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='venta_productos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'venta_producto'
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'
        indexes = [
            models.Index(fields=['venta']),
            models.Index(fields=['tienda_producto']),
        ]
    
    def __str__(self):
        return f"{self.cantidad}x {self.tienda_producto.producto.nombre} (Venta #{self.venta.id})"
    
    def save(self, *args, **kwargs):
        """
        Calcula el subtotal automáticamente al guardar.
        """
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        # Actualizar el total de la venta
        self.venta.calcular_total()
        self.venta.save()