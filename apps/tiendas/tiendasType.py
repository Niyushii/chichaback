from graphene_django import DjangoObjectType
import graphene
from .models import Tienda

class TiendaType(DjangoObjectType):
    foto_perfil_url = graphene.String()
    codigo_qr_url = graphene.String()

    class Meta:
        model = Tienda
        fields = "__all__"
        description = "Representa una tienda gestionada por un usuario."
    
    def resolve_foto_perfil_url(self, info):
        if self.foto_perfil:
            return info.context.build_absolute_uri(self.foto_perfil.url)
        return None

    def resolve_codigo_qr_url(self, info):
        if self.codigo_qr:
            return info.context.build_absolute_uri(self.codigo_qr.url)
        return None
