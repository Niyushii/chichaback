import graphene
from graphql import GraphQLError
from django.utils import timezone
from .models import Favoritos
from .favoritosType import FavoritoType
from apps.usuarios.utils import requiere_autenticacion
from apps.productos.models import TiendaProducto
from core.models import Estado

# ============= MUTATIONS =============

class AgregarFavorito(graphene.Mutation):
    """
    Agrega un producto a la lista de favoritos del usuario.
    Si ya existe, no hace nada (idempotente).
    """
    class Arguments:
        tienda_producto_id = graphene.ID(required=True)
    
    favorito = graphene.Field(FavoritoType)
    mensaje = graphene.String()
    ya_existia = graphene.Boolean()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, tienda_producto_id, **kwargs):
        usuario = kwargs['current_user']
        
        # Verificar que el producto exista
        try:
            tienda_producto = TiendaProducto.objects.get(
                pk=tienda_producto_id,
                fecha_eliminacion__isnull=True
            )
        except TiendaProducto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")
        
        # Verificar si ya existe en favoritos (incluso si fue eliminado)
        favorito_existente = Favoritos.objects.filter(
            usuario=usuario,
            tienda_producto=tienda_producto
        ).first()
        
        if favorito_existente:
            # Si fue eliminado anteriormente, reactivarlo
            if favorito_existente.fecha_eliminacion:
                favorito_existente.fecha_eliminacion = None
                favorito_existente.estado = Estado.get_activo()
                favorito_existente.save()
                
                return AgregarFavorito(
                    favorito=favorito_existente,
                    mensaje="Producto agregado nuevamente a favoritos",
                    ya_existia=True
                )
            else:
                # Ya está en favoritos activos
                return AgregarFavorito(
                    favorito=favorito_existente,
                    mensaje="Este producto ya está en tus favoritos",
                    ya_existia=True
                )
        
        # Crear nuevo favorito
        favorito = Favoritos(
            usuario=usuario,
            tienda_producto=tienda_producto,
            estado=Estado.get_activo()
        )
        favorito.save()
        
        return AgregarFavorito(
            favorito=favorito,
            mensaje="Producto agregado a favoritos exitosamente",
            ya_existia=False
        )


class EliminarFavorito(graphene.Mutation):
    """
    Elimina un producto de la lista de favoritos del usuario.
    Realiza soft delete.
    """
    class Arguments:
        tienda_producto_id = graphene.ID(required=True)
    
    ok = graphene.Boolean()
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, tienda_producto_id, **kwargs):
        usuario = kwargs['current_user']
        
        # Buscar el favorito
        try:
            favorito = Favoritos.objects.get(
                usuario=usuario,
                tienda_producto_id=tienda_producto_id,
                fecha_eliminacion__isnull=True
            )
        except Favoritos.DoesNotExist:
            raise GraphQLError("Este producto no está en tus favoritos")
        
        # Soft delete
        favorito.fecha_eliminacion = timezone.now()
        favorito.estado = Estado.get_inactivo()
        favorito.save()
        
        return EliminarFavorito(
            ok=True,
            mensaje="Producto eliminado de favoritos"
        )


class LimpiarFavoritos(graphene.Mutation):
    """
    Elimina todos los favoritos del usuario (soft delete).
    """
    ok = graphene.Boolean()
    mensaje = graphene.String()
    cantidad_eliminada = graphene.Int()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, **kwargs):
        usuario = kwargs['current_user']
        
        # Obtener todos los favoritos activos
        favoritos = Favoritos.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True
        )
        
        cantidad = favoritos.count()
        
        if cantidad == 0:
            return LimpiarFavoritos(
                ok=True,
                mensaje="No tienes favoritos para eliminar",
                cantidad_eliminada=0
            )
        
        # Soft delete en masa
        favoritos.update(
            fecha_eliminacion=timezone.now(),
            estado=Estado.get_inactivo()
        )
        
        return LimpiarFavoritos(
            ok=True,
            mensaje=f"Se eliminaron {cantidad} productos de tus favoritos",
            cantidad_eliminada=cantidad
        )


class ToggleFavorito(graphene.Mutation):
    """
    Agrega o elimina un producto de favoritos según su estado actual.
    Útil para botones de favorito que cambian de estado.
    """
    class Arguments:
        tienda_producto_id = graphene.ID(required=True)
    
    favorito = graphene.Field(FavoritoType)
    accion = graphene.String()  # "agregado" o "eliminado"
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, tienda_producto_id, **kwargs):
        usuario = kwargs['current_user']
        
        # Verificar que el producto exista
        try:
            tienda_producto = TiendaProducto.objects.get(
                pk=tienda_producto_id,
                fecha_eliminacion__isnull=True
            )
        except TiendaProducto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")
        
        # Buscar favorito existente
        favorito = Favoritos.objects.filter(
            usuario=usuario,
            tienda_producto=tienda_producto,
            fecha_eliminacion__isnull=True
        ).first()
        
        if favorito:
            # Eliminar de favoritos
            favorito.fecha_eliminacion = timezone.now()
            favorito.estado = Estado.get_inactivo()
            favorito.save()
            
            return ToggleFavorito(
                favorito=None,
                accion="eliminado",
                mensaje="Producto eliminado de favoritos"
            )
        else:
            # Agregar a favoritos (o reactivar si fue eliminado)
            favorito_eliminado = Favoritos.objects.filter(
                usuario=usuario,
                tienda_producto=tienda_producto
            ).first()
            
            if favorito_eliminado:
                # Reactivar
                favorito_eliminado.fecha_eliminacion = None
                favorito_eliminado.estado = Estado.get_activo()
                favorito_eliminado.save()
                nuevo_favorito = favorito_eliminado
            else:
                # Crear nuevo
                nuevo_favorito = Favoritos.objects.create(
                    usuario=usuario,
                    tienda_producto=tienda_producto,
                    estado=Estado.get_activo()
                )
            
            return ToggleFavorito(
                favorito=nuevo_favorito,
                accion="agregado",
                mensaje="Producto agregado a favoritos"
            )


# ============= MUTATION CLASS =============

class FavoritosMutaciones(graphene.ObjectType):
    agregar_favorito = AgregarFavorito.Field()
    eliminar_favorito = EliminarFavorito.Field()
    limpiar_favoritos = LimpiarFavoritos.Field()
    toggle_favorito = ToggleFavorito.Field()