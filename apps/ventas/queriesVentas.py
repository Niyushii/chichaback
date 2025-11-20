import graphene
from graphql import GraphQLError
from .ventasType import VentaType
from .models import Venta
from apps.usuarios.utils import requiere_autenticacion
from core.models import Estado

class VentasQueries(graphene.ObjectType):
    mis_compras = graphene.List(VentaType)
    ventas_de_mi_tienda = graphene.List(
        VentaType,
        tienda_id=graphene.ID(required=True)
    )
    ventas_pendientes_tienda = graphene.List(VentaType, tienda_id=graphene.ID(required=True))
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_mis_compras(self, info, **kwargs):
        usuario = kwargs['current_user']
        return Venta.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True
        ).select_related('tienda').prefetch_related('detalles')
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_ventas_de_mi_tienda(self, info, tienda_id, **kwargs):
        usuario = kwargs['current_user']
        
        return Venta.objects.filter(
            tienda_id=tienda_id,
            tienda__propietario=usuario,
            fecha_eliminacion__isnull=True
        ).select_related('usuario').prefetch_related('detalles')
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_ventas_pendientes_tienda(self, info, tienda_id, **kwargs):
        usuario = kwargs['current_user']
        
        return Venta.objects.filter(
            tienda_id=tienda_id,
            tienda__propietario=usuario,
            estado__nombre=Estado.PENDIENTE,
            fecha_eliminacion__isnull=True
        ).select_related('usuario').prefetch_related('detalles')