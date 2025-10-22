from graphene_django import DjangoObjectType
from .models import Producto, Talla, TiendaProducto, ImagenProducto

class ProductoType(DjangoObjectType):
    class Meta:
        model = Producto
        fields = "__all__"
        description = "Representa un producto disponible en la tienda."

class TallaType(DjangoObjectType):
    class Meta:
        model = Talla
        fields = "__all__"
        description = "Representa una talla disponible para un producto."

class TiendaProductoType(DjangoObjectType):
    class Meta:
        model = TiendaProducto
        fields = "__all__"
        description = "Representa la relación entre un producto y una tienda."

class ImagenProductoType(DjangoObjectType):
    class Meta:
        model = ImagenProducto
        fields = "__all__"
        description = "Representa una imagen asociada a un producto."