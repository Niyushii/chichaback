import graphene
from graphene_django import DjangoObjectType
from .models import Favoritos

class FavoritoType(DjangoObjectType):
    class Meta:
        model = Favoritos
        fields = "__all__"
        description = "Representa un producto favorito guardado por un usuario."
        
class EstadisticasFavoritosType(graphene.ObjectType):
    total = graphene.Int(description="Total de favoritos activos")
    recientes_7_dias = graphene.Int(description="Favoritos agregados en los últimos 7 días")
    tienda_favorita = graphene.String(description="Tienda con más productos en favoritos")
    tienda_favorita_cantidad = graphene.Int(description="Cantidad de productos de la tienda favorita")
    categoria_favorita = graphene.String(description="Categoría con más productos en favoritos")
    categoria_favorita_cantidad = graphene.Int(description="Cantidad de productos de la categoría favorita")
    precio_promedio = graphene.Float(description="Precio promedio de productos en favoritos")
    precio_minimo = graphene.Float(description="Precio mínimo en favoritos")
    precio_maximo = graphene.Float(description="Precio máximo en favoritos")