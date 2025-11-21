import graphene
import cloudinary.uploader
from graphql import GraphQLError
from django.utils import timezone
from .models import Venta, VentaProducto
from apps.productos.models import TiendaProducto
from apps.usuarios.models import Usuario, Notificacion
from apps.usuarios.utils import requiere_autenticacion
from core.models import Estado
from core.graphql_scalars import Upload

# ============= CREAR VENTA CON COMPROBANTE =============

class CrearVentaInput(graphene.InputObjectType):
    tienda_producto_id = graphene.ID(required=True)
    cantidad = graphene.Int(default_value=1)

class CrearVenta(graphene.Mutation):
    class Arguments:
        input = CrearVentaInput(required=True)
        comprobante = Upload(required=True)  # ← Imagen del comprobante
    
    venta = graphene.Field('apps.ventas.ventasType.VentaType')
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, comprobante, **kwargs):
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


        
        # Subir comprobante a Cloudinary
        resultado = cloudinary.uploader.upload(
            comprobante,
            folder="comprobantes/"
        )
        
        # Calcular total
        precio_unitario = tp.precio
        subtotal = precio_unitario * input.cantidad
        
        # Crear venta con estado "pendiente"
        venta = Venta.objects.create(
            usuario=usuario,
            tienda=tp.tienda,
            total=subtotal,
            comprobante=resultado['secure_url'],
            estado=Estado.get_pendiente()
        )
        
        # Crear detalle
        VentaProducto.objects.create(
            venta=venta,
            tienda_producto=tp,
            cantidad=input.cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
            estado=Estado.get_pendiente()
        )
        
        # Cambiar estado del producto a "reservado"
        tp.estado = Estado.get_reservado()
        tp.save()
        
        # ✅ CREAR NOTIFICACIÓN PARA EL VENDEDOR
        Notificacion.objects.create(
            usuario=tp.tienda.propietario,
            tipo='venta_pendiente',
            titulo='Nueva venta pendiente',
            mensaje=f'{usuario.username} ha comprado {tp.producto.nombre}. Verifica el comprobante.',
            venta_relacionada=venta
        )
        
        return CrearVenta(
            venta=venta,
            mensaje="Venta registrada. Esperando confirmación del vendedor."
        )


# ============= CONFIRMAR/RECHAZAR VENTA =============

class ResponderVenta(graphene.Mutation):
    """El vendedor confirma o rechaza el pago"""
    class Arguments:
        venta_id = graphene.ID(required=True)
        aceptar = graphene.Boolean(required=True)
        motivo_rechazo = graphene.String()  # Opcional, si se rechaza
    
    ok = graphene.Boolean()
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, venta_id, aceptar, motivo_rechazo=None, **kwargs):
        usuario = kwargs['current_user']
        
        try:
            venta = Venta.objects.get(pk=venta_id)
        except Venta.DoesNotExist:
            raise GraphQLError("Venta no encontrada")
        
        # Verificar que sea el dueño de la tienda
        if venta.tienda.propietario != usuario:
            raise GraphQLError("No autorizado")
        
        # Verificar que la venta esté pendiente
        if venta.estado.nombre != Estado.PENDIENTE:
            raise GraphQLError("Esta venta ya fue procesada")
        
        if aceptar:
            # ✅ ACEPTAR VENTA
            venta.estado = Estado.get_completado()
            venta.save()
            
            # Actualizar stock y estado de productos
            for detalle in venta.detalles.all():
                tp = detalle.tienda_producto
                tp.stock -= detalle.cantidad
                
                # Marcar como vendido si ya no hay stock
                if tp.stock <= 0:
                    tp.estado = Estado.get_vendido()
                else:
                    tp.estado = Estado.get_disponible()
                
                tp.save()
                detalle.estado = Estado.get_completado()
                detalle.save()
            
            # Notificar al comprador
            Notificacion.objects.create(
                usuario=venta.usuario,
                tipo='venta_confirmada',
                titulo='¡Compra confirmada!',
                mensaje=f'Tu compra en {venta.tienda.nombre} fue confirmada.',
                venta_relacionada=venta
            )
            
            return ResponderVenta(ok=True, mensaje="Venta confirmada exitosamente")
        
        else:
            # ❌ RECHAZAR VENTA
            venta.estado = Estado.get_rechazado()
            venta.save()
            
            # Liberar productos (volver a disponible)
            for detalle in venta.detalles.all():
                tp = detalle.tienda_producto
                tp.estado = Estado.get_disponible()
                tp.save()
                
                detalle.estado = Estado.get_rechazado()
                detalle.save()
            
            # Notificar al comprador
            mensaje_rechazo = motivo_rechazo or "El vendedor no pudo verificar tu pago."
            Notificacion.objects.create(
                usuario=venta.usuario,
                tipo='venta_rechazada',
                titulo='Compra rechazada',
                mensaje=f'Tu compra fue rechazada. Motivo: {mensaje_rechazo}',
                venta_relacionada=venta
            )
            
            return ResponderVenta(ok=True, mensaje="Venta rechazada")


# ============= CANCELAR VENTA (COMPRADOR) =============

class CancelarVenta(graphene.Mutation):
    """El comprador puede cancelar antes de que el vendedor responda"""
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
        
        # Verificar que sea el comprador
        if venta.usuario != usuario:
            raise GraphQLError("No autorizado")
        
        # Solo se puede cancelar si está pendiente
        if venta.estado.nombre != Estado.PENDIENTE:
            raise GraphQLError("No puedes cancelar esta venta")
        
        venta.estado = Estado.get_cancelado()
        venta.save()
        
        # Liberar productos
        for detalle in venta.detalles.all():
            tp = detalle.tienda_producto
            tp.estado = Estado.get_disponible()
            tp.save()
            detalle.estado = Estado.get_cancelado()
            detalle.save()
        
        return CancelarVenta(ok=True, mensaje="Venta cancelada")


class VentasMutaciones(graphene.ObjectType):
    crear_venta = CrearVenta.Field()
    responder_venta = ResponderVenta.Field()
    cancelar_venta = CancelarVenta.Field()