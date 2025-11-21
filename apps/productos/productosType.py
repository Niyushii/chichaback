from graphene_django import DjangoObjectType
import graphene
from .models import Producto, Talla, TiendaProducto, ImagenProducto
from apps.tiendas.tiendasType import TiendaType

class ProductoType(DjangoObjectType):
    class Meta:
        model = Producto
        fields = "__all__"

class TallaType(DjangoObjectType):
    class Meta:
        model = Talla
        fields = "__all__"

class TiendaProductoType(DjangoObjectType):
    tienda = graphene.Field(TiendaType)
    producto = graphene.Field(lambda: ProductoType)
    talla = graphene.Field(lambda: TallaType)
    imagenes = graphene.List(lambda: ImagenProductoType)
    imagenes_urls = graphene.List(graphene.String)

    class Meta:
        model = TiendaProducto
        fields = "__all__"

    def resolve_imagenes_urls(self, info):
        return [img.archivo for img in self.imagenes.all() if img.archivo]

    def resolve_imagenes(self, info):
        return self.imagenes.all()


class ImagenProductoType(DjangoObjectType):
    archivo_url = graphene.String()

    class Meta:
        model = ImagenProducto
        fields = "__all__"

    def resolve_archivo_url(self, info):
        if self.archivo:
            return info.context.build_absolute_uri(self.archivo.url)
        return None
