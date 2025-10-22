from graphene_django import DjangoObjectType
from .models import Venta, VentaProducto

class VentaType(DjangoObjectType):
    class Meta:
        model = Venta
        fields = "__all__"
        description = "Representa una venta realizada en la tienda."

class VentaProductoType(DjangoObjectType):
    class Meta:
        model = VentaProducto
        fields = "__all__"
        description = "Representa un producto vendido en una venta."