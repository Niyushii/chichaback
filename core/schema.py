import graphene
from apps.usuarios.schemaUsuarios import Query as UsuariosQuery, Mutation as UsuariosMutation
from apps.categorias.schemaCategorias import Query as CategoriasQuery, Mutation as CategoriasMutation
from apps.tiendas.schemaTiendas import Query as TiendasQuery, Mutation as TiendasMutation
from apps.productos.schemaProductos import Query as ProductosQuery, Mutation as ProductosMutation
from core.coreType import EstadoType


# Clases que unifican los esquemas de las distintas aplicaciones
class Query(
    UsuariosQuery,
    CategoriasQuery,
    TiendasQuery,
    ProductosQuery,
    graphene.ObjectType
):
    pass

class Mutation(
    UsuariosMutation,
    CategoriasMutation,
    TiendasMutation,
    ProductosMutation,
    graphene.ObjectType
):
    pass

# Schema principal que une todas las consultas y mutaciones

schema = graphene.Schema(query=Query, mutation=Mutation)