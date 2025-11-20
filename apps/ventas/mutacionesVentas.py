import graphene
from graphql import GraphQLError
from django.utils import timezone
from .models import Venta, VentaProducto
from apps.productos.models import TiendaProducto
from apps.usuarios.utils import requiere_autenticacion
from core.models import Estado

class CrearVentaInput(graphene.InputObjectType):
    tienda_producto_id = graphene.ID(required=True)
    cantidad = graphene.Int(default_value=1)
    comprobante = graphene.String()  # URL del comprobante subido

class CrearVenta(graphene.Mutation):
    class Arguments:
        input = CrearVentaInput(required=True)
    
    venta = graphene.Field('apps.ventas.ventasType.VentaType')
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, **kwargs):
        usuario = kwargs['current_user']
        
        # Verificar producto
        try:
            tp = TiendaProducto.objects.get(
                pk=input.tienda_producto_id,
                fecha_eliminacion__isnull=True
            )
        except TiendaProducto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")
        
        # Verificar stock
        if tp.stock < input.cantidad:
            raise GraphQLError("Stock insuficiente")
        
        # Calcular total
        precio_unitario = tp.precio
        subtotal = precio_unitario * input.cantidad
        
        # Crear venta con estado "pendiente"
        venta = Venta.objects.create(
            usuario=usuario,
            tienda=tp.tienda,
            total=subtotal,
            estado=Estado.objects.get(nombre='pendiente')  # ← NUEVO ESTADO
        )
        
        # Crear detalle
        VentaProducto.objects.create(
            venta=venta,
            tienda_producto=tp,
            cantidad=input.cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
            estado=Estado.objects.get(nombre='pendiente')
        )
        
        # Actualizar estado del producto a "pendiente"
        tp.estado = Estado.objects.get(nombre='pendiente')
        tp.save()
        
        return CrearVenta(
            venta=venta,
            mensaje="Venta registrada. Esperando confirmación del vendedor."
        )


class ConfirmarVenta(graphene.Mutation):
    """El vendedor confirma el pago y actualiza el stock"""
    class Arguments:
        venta_id = graphene.ID(required=True)
    
    ok = graphene.Boolean()
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, venta_id, **kwargs):
        usuario = kwargs['current_user']
        
        try:
            venta = Venta.objects.get(pk=venta_id)
        except Venta.DoesNotExist:
            raise GraphQLError("Venta no encontrada")
        
        # Verificar que sea el dueño de la tienda
        if venta.tienda.propietario != usuario:
            raise GraphQLError("No autorizado")
        
        # Actualizar estado de venta
        venta.estado = Estado.objects.get(nombre='completado')
        venta.save()
        
        # Actualizar stock y estado de productos vendidos
        for detalle in venta.detalles.all():
            tp = detalle.tienda_producto
            tp.stock -= detalle.cantidad
            tp.estado = Estado.get_activo() if tp.stock > 0 else Estado.get_inactivo()
            tp.save()
            
            detalle.estado = Estado.objects.get(nombre='completado')
            detalle.save()
        
        return ConfirmarVenta(
            ok=True,
            mensaje="Venta confirmada y stock actualizado"
        )


class VentasMutaciones(graphene.ObjectType):
    crear_venta = CrearVenta.Field()
    confirmar_venta = ConfirmarVenta.Field()