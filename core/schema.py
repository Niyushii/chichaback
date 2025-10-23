import graphene
from apps.usuarios.schemaUsuarios import Query as UsuariosQuery, Mutation as UsuariosMutation

# Clases que unifican los esquemas de las distintas aplicaciones
class Query(
    UsuariosQuery,
    graphene.ObjectType
):
    pass

class Mutation(
    UsuariosMutation,
    graphene.ObjectType
):
    pass

# Schema principal que une todas las consultas y mutaciones

schema = graphene.Schema(query=Query, mutation=Mutation)