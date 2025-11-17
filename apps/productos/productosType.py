from graphene_django import DjangoObjectType
import graphene
from .models import Producto, Talla, TiendaProducto, ImagenProducto

class ProductoType(DjangoObjectType):
    class Meta:
        model = Producto
        fields = "__all__"

class TallaType(DjangoObjectType):
    class Meta:
        model = Talla
        fields = "__all__"

class TiendaProductoType(DjangoObjectType):
    imagenes_urls = graphene.List(graphene.String)

    class Meta:
        model = TiendaProducto
        fields = "__all__"

    def resolve_imagenes_urls(self, info):
        urls = []
        for img in self.imagenes.all():
            if img.archivo:
                urls.append(info.context.build_absolute_uri(img.archivo.url))
        return urls

class ImagenProductoType(DjangoObjectType):
    archivo_url = graphene.String()

    class Meta:
        model = ImagenProducto
        fields = "__all__"

    def resolve_archivo_url(self, info):
        if self.archivo:
            return info.context.build_absolute_uri(self.archivo.url)
        return None
