import graphene
from .queriesFavoritos import FavoritosQueries
from .mutacionesFavoritos import FavoritosMutaciones

class Query(FavoritosQueries):
    pass

class Mutation(FavoritosMutaciones):
    pass