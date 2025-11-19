from graphene_django import DjangoObjectType
import graphene
from .models import Tienda

class TiendaType(DjangoObjectType):
    class Meta:
        model = Tienda
        fields = "__all__"
        description = "Representa una tienda gestionada por un usuario."
