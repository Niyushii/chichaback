import graphene
from .queriesTiendas import TiendasQueries
from .mutacionesTiendas import TiendasMutaciones

class Query(TiendasQueries):
    pass

class Mutation(TiendasMutaciones):
    pass