from graphene_django import DjangoObjectType
from .models import Estado

class EstadoType(DjangoObjectType):
    class Meta:
        model = Estado
        fields = "__all__"
        description = "Representa un estado en el sistema."