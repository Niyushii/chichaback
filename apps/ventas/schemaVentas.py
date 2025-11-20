import graphene
from .queriesVentas import VentasQueries
from .mutacionesVentas import VentasMutaciones

class Query(VentasQueries):
    pass

class Mutation(VentasMutaciones):
    pass