import graphene
from .queriesCategorias import CategoriasQueries
from .mutacionesCategorias import CategoriasMutaciones

class Query(CategoriasQueries):
    pass

class Mutation(CategoriasMutaciones):
    pass