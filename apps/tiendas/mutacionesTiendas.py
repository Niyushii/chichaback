import graphene
from graphql import GraphQLError
from django.utils import timezone
from .models import Tienda
from .tiendasType import TiendaType
from apps.usuarios.utils import requiere_autenticacion
from apps.usuarios.models import Usuario
from core.models import Estado
from core.graphql_scalars import Upload

# ============= INPUT TYPES =============
class CrearTiendaInput(graphene.InputObjectType):
    nombre = graphene.String(required=True)
    descripcion = graphene.String()
    telefono = graphene.String()
    direccion = graphene.String()
    foto_perfil = Upload()
    codigo_qr = Upload()

class EditarTiendaInput(graphene.InputObjectType):
    nombre = graphene.String()
    descripcion = graphene.String()
    telefono = graphene.String()
    direccion = graphene.String()
    foto_perfil = Upload()
    codigo_qr = Upload()

# ============= MUTACIONS =============
class CrearTienda(graphene.Mutation):
    class Arguments:
        input = CrearTiendaInput(required=True)
    
    tienda = graphene.Field(TiendaType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, **kwargs):
        usuario = kwargs['current_user']
        
        # Verificar que el nombre no esté duplicado para este usuario
        if Tienda.objects.filter(
            propietario=usuario,
            nombre__iexact=input.nombre,
            fecha_eliminacion__isnull=True
        ).exists():
            raise GraphQLError("Ya tienes una tienda con ese nombre")
        
        # Crear tienda
        tienda = Tienda(
            propietario=usuario,
            nombre=input.nombre,
            descripcion=input.descripcion,
            telefono=input.telefono,
            direccion=input.direccion,
            estado=Estado.get_activo()
        )
        
        tienda.save()
        
        # Manejo de imágenes (foto_perfil y codigo_qr) se realiza mediante endpoints REST separados
        if input.foto_perfil:
            tienda.foto_perfil = input.foto_perfil
        
        if input.codigo_qr:
            tienda.codigo_qr = input.codigo_qr
        
        tienda.save()
        
        # Convertir al usuario en vendedor si es su primera tienda
        if not usuario.is_seller:
            usuario.is_seller = True
            usuario.save()
        
        return CrearTienda(
            tienda=tienda,
            mensaje=f"Tienda '{tienda.nombre}' creada exitosamente. ¡Ahora eres vendedor!"
        )

class EditarTienda(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = EditarTiendaInput(required=True)
    
    tienda = graphene.Field(TiendaType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario', 'moderador', 'superadmin'])
    def mutate(self, info, id, input, **kwargs):
        usuario_actual = kwargs['current_user']
        user_type = kwargs['user_type']
        
        try:
            tienda = Tienda.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")
        
        # Verificar permisos: solo el propietario o un moderador pueden editar
        if user_type == 'usuario' and tienda.propietario.id != usuario_actual.id:
            raise GraphQLError("No tienes permiso para editar esta tienda")
        
        # Actualizar campos de texto si se proporcionan
        if input.nombre:
            # Verificar duplicados (excluyendo la actual)
            if Tienda.objects.filter(
                propietario=tienda.propietario,
                nombre__iexact=input.nombre,
                fecha_eliminacion__isnull=True
            ).exclude(pk=id).exists():
                raise GraphQLError("Ya tienes otra tienda con ese nombre")
            tienda.nombre = input.nombre
        
        if input.descripcion is not None:
            tienda.descripcion = input.descripcion
        
        if input.telefono is not None:
            tienda.telefono = input.telefono
        
        if input.direccion is not None:
            tienda.direccion = input.direccion
        
        # Actualizar imágenes si se proporcionan
        if input.foto_perfil:
            if tienda.foto_perfil:
                tienda.foto_perfil.delete(save=False)
            tienda.foto_perfil = input.foto_perfil
        
        if input.codigo_qr:
            if tienda.codigo_qr:
                tienda.codigo_qr.delete(save=False)
            tienda.codigo_qr = input.codigo_qr 
        
        tienda.save()
        
        return EditarTienda(
            tienda=tienda,
            mensaje="Tienda actualizada exitosamente"
        )

class EliminarTienda(graphene.Mutation):
    # Elimina una tienda, incluyendo el soft delete de sus productos activos.
    class Arguments:
        id = graphene.ID(required=True)
    
    ok = graphene.Boolean()
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario', 'moderador', 'superadmin'])
    def mutate(self, info, id, **kwargs):
        usuario_actual = kwargs['current_user']
        user_type = kwargs['user_type']
        
        try:
            tienda = Tienda.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")
        
        # Verificar permisos
        if user_type == 'usuario' and tienda.propietario.id != usuario_actual.id:
            raise GraphQLError("No tienes permiso para eliminar esta tienda")
        
        # Eliminar todos los productos activos de esta tienda
        productos_activos = tienda.productos.filter(fecha_eliminacion__isnull=True)
        if productos_activos.exists():
            productos_activos.update(
                fecha_eliminacion=timezone.now(),
                estado=Estado.get_inactivo()
            )
        
        # Eliminar imágenes de la tienda 
        if tienda.foto_perfil:
            tienda.foto_perfil.delete()
        if tienda.codigo_qr:
            tienda.codigo_qr.delete()
        
        # Soft delete de la tienda
        tienda.fecha_eliminacion = timezone.now()
        tienda.estado = Estado.get_inactivo()
        tienda.save()
        
        # Si el usuario ya no tiene tiendas activas se quita el rol de vendedor
        if user_type == 'usuario':
            if not Tienda.objects.filter(
                propietario=tienda.propietario,
                fecha_eliminacion__isnull=True
            ).exists():
                propietario = Usuario.objects.get(pk=tienda.propietario.id)
                propietario.is_seller = False
                propietario.save()
        
        return EliminarTienda(
            ok=True,
            mensaje=f"Tienda '{tienda.nombre}' y sus {productos_activos.count()} productos asociados han sido eliminados exitosamente"
        )
        
# Eliminar Imagenes
class EliminarFotoPerfil(graphene.Mutation):
    class Arguments:
        tienda_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario','moderador','superadmin'])
    def mutate(self, info, tienda_id, **kwargs):
        usuario = kwargs["current_user"]
        user_type = kwargs["user_type"]

        try:
            tienda = Tienda.objects.get(pk=tienda_id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        if user_type == "usuario" and tienda.propietario.id != usuario.id:
            raise GraphQLError("No tienes permiso")

        if tienda.foto_perfil:
            tienda.foto_perfil.delete()
            tienda.foto_perfil = None
            tienda.save()

        return EliminarFotoPerfil(ok=True, mensaje="Foto eliminada")


class EliminarCodigoQR(graphene.Mutation):
    class Arguments:
        tienda_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario','moderador','superadmin'])
    def mutate(self, info, tienda_id, **kwargs):
        usuario = kwargs["current_user"]
        user_type = kwargs["user_type"]

        try:
            tienda = Tienda.objects.get(pk=tienda_id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        if user_type == "usuario" and tienda.propietario.id != usuario.id:
            raise GraphQLError("No tienes permiso")

        if tienda.codigo_qr:
            tienda.codigo_qr.delete()
            tienda.codigo_qr = None
            tienda.save()

        return EliminarCodigoQR(ok=True, mensaje="Código QR eliminado")

# ============= MUTATION CLASS =============
class TiendasMutaciones(graphene.ObjectType):
    crear_tienda = CrearTienda.Field()
    editar_tienda = EditarTienda.Field()
    eliminar_tienda = EliminarTienda.Field()
    eliminar_foto_perfil = EliminarFotoPerfil.Field()
    eliminar_codigo_qr = EliminarCodigoQR.Field()