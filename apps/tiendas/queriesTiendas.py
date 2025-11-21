import graphene
from graphql import GraphQLError
from graphene_django.types import DjangoObjectType

from .models import Tienda
from .tiendasType import TiendaType
from apps.usuarios.utils import requiere_autenticacion


# ============================================
# QUERIES PÚBLICAS
# ============================================

class QueryTiendasPublicas(graphene.ObjectType):
    tiendas_publicas = graphene.List(TiendaType)
    tienda_publica = graphene.Field(TiendaType, id=graphene.ID(required=True))
    tiendas_por_vendedor = graphene.List(TiendaType, vendedor_id=graphene.ID(required=True))
    buscar_tiendas = graphene.List(TiendaType, nombre=graphene.String(required=True))

    def resolve_tiendas_publicas(self, info):
        return Tienda.objects.filter(fecha_eliminacion__isnull=True, estado__nombre__iexact="Activo")

    def resolve_tienda_publica(self, info, id):
        try:
            return Tienda.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

    def resolve_tiendas_por_vendedor(self, info, vendedor_id):
        return Tienda.objects.filter(propietario_id=vendedor_id, fecha_eliminacion__isnull=True)

    def resolve_buscar_tiendas(self, info, nombre):
        return Tienda.objects.filter(
            nombre__icontains=nombre,
            fecha_eliminacion__isnull=True
        )


# ============================================
# QUERIES PROTEGIDAS (TOKEN NECESARIO)
# ============================================

class QueryTiendasPrivadas(graphene.ObjectType):
    mis_tiendas = graphene.List(TiendaType)
    mi_tienda = graphene.Field(TiendaType, id=graphene.ID(required=True))
    tiendas_admin = graphene.List(TiendaType)

    @requiere_autenticacion(user_types=['usuario'])
    def resolve_mis_tiendas(self, info, **kwargs):
        usuario = kwargs["current_user"]
        return Tienda.objects.filter(propietario=usuario, fecha_eliminacion__isnull=True)

    @requiere_autenticacion(user_types=['usuario'])
    def resolve_mi_tienda(self, info, id, **kwargs):
        usuario = kwargs["current_user"]
        try:
            tienda = Tienda.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        if tienda.propietario != usuario:
            raise GraphQLError("No tienes permiso para ver esta tienda")

        return tienda

    @requiere_autenticacion(user_types=['moderador','superadmin'])
    def resolve_tiendas_admin(self, info, **kwargs):
        return Tienda.objects.filter(fecha_eliminacion__isnull=True)

class TiendasQueries(
    QueryTiendasPublicas,
    QueryTiendasPrivadas,
    graphene.ObjectType
):
    pass