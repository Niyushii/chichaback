import graphene
from graphene_django import DjangoObjectType
from .models import Favorito

class FavoritoType(DjangoObjectType):
    class Meta:
        model = Favorito
        fields = "__all__"
        description = "Representa un producto favorito guardado por un usuario."