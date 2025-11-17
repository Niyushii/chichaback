import graphene
from .mutacionesProductos import ProductosMutaciones
from .queriesProductos import ProductosQuery

class Query(ProductosQuery, graphene.ObjectType):
    pass

class Mutation(ProductosMutaciones, graphene.ObjectType):
    pass