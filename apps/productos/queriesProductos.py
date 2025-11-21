import graphene
from graphql import GraphQLError
from .productosType import ProductoType, TiendaProductoType, TallaType
from .models import Producto, TiendaProducto, Talla
from apps.usuarios.utils import requiere_autenticacion

class ProductosPublicosQuery(graphene.ObjectType):
    todos_productos = graphene.List(ProductoType, limit=graphene.Int(default_value=20), offset=graphene.Int(default_value=0))
    producto_por_id = graphene.Field(ProductoType, id=graphene.ID(required=True))
    productos_de_tienda = graphene.List(TiendaProductoType, tienda_id=graphene.ID(required=True))
    buscar_productos = graphene.List(ProductoType, nombre=graphene.String(required=True), limit=graphene.Int(default_value=20), offset=graphene.Int(default_value=0))
    tallas = graphene.List(TallaType)

    # ⭐ NUEVA QUERY
    productos_por_categoria = graphene.List(
        TiendaProductoType,
        categoria_id=graphene.ID(required=True)
    )

    def resolve_todos_productos(self, info, limit=20, offset=0):
        return Producto.objects.filter(fecha_eliminacion__isnull=True)[offset:offset + limit]

    def resolve_producto_por_id(self, info, id):
        try:
            return Producto.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Producto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")

    def resolve_productos_de_tienda(self, info, tienda_id):
        return TiendaProducto.objects.filter(
            tienda_id=tienda_id,
            fecha_eliminacion__isnull=True
        )

    def resolve_buscar_productos(self, info, nombre, limit=20, offset=0):
        return Producto.objects.filter(
            nombre__icontains=nombre,
            fecha_eliminacion__isnull=True
        )[offset:offset + limit]

    def resolve_tallas(self, info):
        return Talla.objects.filter(fecha_eliminacion__isnull=True)

    # ⭐ RESOLVER NUEVO CON SUBCATEGORÍAS
    def resolve_productos_por_categoria(self, info, categoria_id):
        from apps.categorias.models import Categoria

        try:
            categoria = Categoria.objects.get(pk=categoria_id, fecha_eliminacion__isnull=True)
        except Categoria.DoesNotExist:
            raise GraphQLError("Categoría no encontrada")

        # IDs de categoría + subcategorías
        ids_categorias = [categoria.id]
        ids_categorias.extend(list(categoria.subcategorias.values_list("id", flat=True)))

        return TiendaProducto.objects.filter(
            producto__categoria_id__in=ids_categorias,
            fecha_eliminacion__isnull=True
        )


# Query Privada para vendedores autenticados

class ProductosPrivadosQuery(graphene.ObjectType):
    mis_productos = graphene.List(TiendaProductoType)

    @requiere_autenticacion(user_types=['usuario'])
    def resolve_mis_productos(self, info, **kwargs):
        usuario = kwargs["current_user"]
        return TiendaProducto.objects.filter(
            tienda__propietario=usuario,
            fecha_eliminacion__isnull=True
        )

class ProductosQuery(ProductosPublicosQuery, ProductosPrivadosQuery):
    pass

