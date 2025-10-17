import graphene
from graphene_django import DjangoObjectType
from .models import Categoria

class CategoriaType(DjangoObjectType):
    class Meta:
        model = Categoria
        fields = "__all__"
        description = "Representa una categoría de productos en el sistema."