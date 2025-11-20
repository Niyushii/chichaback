import graphene
from apps.usuarios.schemaUsuarios import Query as UsuariosQuery, Mutation as UsuariosMutation
from apps.categorias.schemaCategorias import Query as CategoriasQuery, Mutation as CategoriasMutation
from apps.tiendas.schemaTiendas import Query as TiendasQuery, Mutation as TiendasMutation
from apps.productos.schemaProductos import Query as ProductosQuery, Mutation as ProductosMutation
from apps.favoritos.schemaFavoritos import Query as FavoritosQuery, Mutation as FavoritosMutation
from apps.ventas.schemaVentas import Query as VentasQuery, Mutation as VentasMutation
from core.coreType import EstadoType


# Clases que unifican los esquemas de las distintas aplicaciones
class Query(
    UsuariosQuery,
    CategoriasQuery,
    TiendasQuery,
    ProductosQuery,
    FavoritosQuery,
    VentasQuery,
    graphene.ObjectType
):
    pass

class Mutation(
    UsuariosMutation,
    CategoriasMutation,
    TiendasMutation,
    ProductosMutation,
    FavoritosMutation,
    VentasMutation,
    graphene.ObjectType
):
    pass

# Schema principal que une todas las consultas y mutaciones

schema = graphene.Schema(query=Query, mutation=Mutation)