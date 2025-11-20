import graphene
from apps.productos.productosType import TiendaProductoType
from apps.tiendas.tiendasType import TiendaType
from apps.productos.models import TiendaProducto
from apps.tiendas.models import Tienda
from django.db.models import Q
from core.models import Estado

class ResultadoBusquedaType(graphene.ObjectType):
    productos = graphene.List(TiendaProductoType)
    tiendas = graphene.List(TiendaType)
    total_productos = graphene.Int()
    total_tiendas = graphene.Int()

class BusquedaQueries(graphene.ObjectType):
    busqueda_general = graphene.Field(
        ResultadoBusquedaType,
        texto=graphene.String(required=True),
        limite_productos=graphene.Int(default_value=20),
        limite_tiendas=graphene.Int(default_value=10)
    )
    
    def resolve_busqueda_general(self, info, texto, limite_productos=20, limite_tiendas=10):
        # Buscar productos
        productos = TiendaProducto.objects.filter(
            Q(producto__nombre__icontains=texto) |
            Q(descripcion__icontains=texto) |
            Q(producto__categoria__nombre__icontains=texto),
            fecha_eliminacion__isnull=True,
            estado__nombre=Estado.DISPONIBLE
        ).select_related('producto', 'tienda', 'talla')[:limite_productos]
        
        # Buscar tiendas
        tiendas = Tienda.objects.filter(
            Q(nombre__icontains=texto) |
            Q(descripcion__icontains=texto),
            fecha_eliminacion__isnull=True
        ).select_related('propietario')[:limite_tiendas]
        
        return ResultadoBusquedaType(
            productos=list(productos),
            tiendas=list(tiendas),
            total_productos=productos.count(),
            total_tiendas=tiendas.count()
        )