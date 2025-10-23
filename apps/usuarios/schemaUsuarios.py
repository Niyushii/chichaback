import graphene
from .queriesUsuarios import UsuariosQueries
from .mutacionesUsuario import UsuariosMutaciones

class Query(UsuariosQueries):
    pass

class Mutation(UsuariosMutaciones):
    pass