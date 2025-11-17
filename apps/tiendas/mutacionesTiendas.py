import graphene
from graphql import GraphQLError
from django.utils import timezone
from .models import Tienda
from .tiendasType import TiendaType
from apps.usuarios.utils import requiere_autenticacion
from apps.usuarios.models import Usuario
from core.models import Estado
from core.graphql_scalars import Upload
from apps.usuarios.models import Auditoria

# ============================================
# INPUT TYPES
# ============================================

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


# ============================================
# MUTACIÓN: CREAR TIENDA
# ============================================

class CrearTienda(graphene.Mutation):
    class Arguments:
        input = CrearTiendaInput(required=True)

    tienda = graphene.Field(TiendaType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, **kwargs):
        usuario = kwargs['current_user']

        # Nombre único por usuario
        if Tienda.objects.filter(
            propietario=usuario,
            nombre__iexact=input.nombre,
            fecha_eliminacion__isnull=True
        ).exists():
            raise GraphQLError("Ya tienes una tienda con ese nombre")

        tienda = Tienda(
            propietario=usuario,
            nombre=input.nombre,
            descripcion=input.descripcion,
            telefono=input.telefono,
            direccion=input.direccion,
            estado=Estado.get_activo()
        )
        tienda.save()

        # IMÁGENES OPCIONALES
        if input.foto_perfil:
            tienda.foto_perfil = input.foto_perfil

        if input.codigo_qr:
            tienda.codigo_qr = input.codigo_qr

        tienda.save()

        # Convertir a vendedor
        if not usuario.is_seller:
            usuario.is_seller = True
            usuario.save()

        return CrearTienda(
            tienda=tienda,
            mensaje=f"Tienda '{tienda.nombre}' creada exitosamente."
        )


# ============================================
# MUTACIÓN: EDITAR TIENDA (PERMISOS CORREGIDOS)
# ============================================

class EditarTienda(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = EditarTiendaInput(required=True)

    tienda = graphene.Field(TiendaType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario', 'moderador', 'superadmin'])
    def mutate(self, info, id, input, **kwargs):
        usuario = kwargs["current_user"]
        rol = kwargs["user_type"]

        try:
            tienda = Tienda.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        # PERMISOS:
        # usuario → solo su tienda
        # moderador y superadmin → pueden editar TODO
        if rol == "usuario" and tienda.propietario.id != usuario.id:
            raise GraphQLError("No tienes permiso para editar esta tienda")

        # Auditoría: registrar si un moderador/admin modifica
        if rol in ["moderador", "superadmin"]:
            Auditoria.registrar(
                usuario=usuario,
                accion="editar_tienda",
                descripcion=f"{usuario.email} editó la tienda {tienda.nombre}"
            )

        # Actualización de campos
        if input.nombre:
            if Tienda.objects.filter(
                propietario=tienda.propietario,
                nombre__iexact=input.nombre,
                fecha_eliminacion__isnull=True
            ).exclude(pk=id).exists():
                raise GraphQLError("Ya existe otra tienda con ese nombre")
            tienda.nombre = input.nombre

        if input.descripcion is not None:
            tienda.descripcion = input.descripcion

        if input.telefono is not None:
            tienda.telefono = input.telefono

        if input.direccion is not None:
            tienda.direccion = input.direccion

        # IMÁGENES
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


# ============================================
# MUTACIÓN: ELIMINAR TIENDA (PERMISOS CORREGIDOS)
# ============================================

class EliminarTienda(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario', 'moderador', 'superadmin'])
    def mutate(self, info, id, **kwargs):
        usuario = kwargs["current_user"]
        rol = kwargs["user_type"]

        try:
            tienda = Tienda.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        # PERMISOS
        if rol == "usuario" and tienda.propietario.id != usuario.id:
            raise GraphQLError("No tienes permiso para eliminar esta tienda")

        # Registrar auditoría (moderador/admin)
        if rol in ["moderador", "superadmin"]:
            Auditoria.registrar(
                usuario=usuario,
                accion="eliminar_tienda",
                descripcion=f"{usuario.email} eliminó la tienda {tienda.nombre}"
            )

        # Soft delete
        tienda.fecha_eliminacion = timezone.now()
        tienda.estado = Estado.get_inactivo()
        tienda.save()

        # Perder rol de vendedor si ya no tiene tiendas
        if rol == "usuario":
            if not Tienda.objects.filter(
                propietario=tienda.propietario,
                fecha_eliminacion__isnull=True
            ).exists():
                propietario = Usuario.objects.get(id=tienda.propietario.id)
                propietario.is_seller = False
                propietario.save()

        return EliminarTienda(
            ok=True,
            mensaje="Tienda eliminada exitosamente"
        )


# ============================================
# MUTACIONES PARA BORRAR IMÁGENES
# ============================================

class EliminarFotoPerfil(graphene.Mutation):
    class Arguments:
        tienda_id = graphene.ID(required=True)

    ok = graphene.Boolean()
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario','moderador','superadmin'])
    def mutate(self, info, tienda_id, **kwargs):
        usuario = kwargs["current_user"]
        rol = kwargs["user_type"]

        try:
            tienda = Tienda.objects.get(pk=tienda_id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        if rol == "usuario" and tienda.propietario.id != usuario.id:
            raise GraphQLError("No tienes permiso")

        if rol in ["moderador", "superadmin"]:
            Auditoria.registrar(
                usuario=usuario,
                accion="eliminar_foto_perfil",
                descripcion=f"{usuario.email} eliminó la foto de perfil de {tienda.nombre}"
            )

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
        rol = kwargs["user_type"]

        try:
            tienda = Tienda.objects.get(pk=tienda_id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        if rol == "usuario" and tienda.propietario.id != usuario.id:
            raise GraphQLError("No tienes permiso")

        if rol in ["moderador", "superadmin"]:
            Auditoria.registrar(
                usuario=usuario,
                accion="eliminar_codigo_qr",
                descripcion=f"{usuario.email} eliminó el código QR de {tienda.nombre}"
            )

        if tienda.codigo_qr:
            tienda.codigo_qr.delete()
            tienda.codigo_qr = None
            tienda.save()

        return EliminarCodigoQR(ok=True, mensaje="Código QR eliminado")


# ============================================
# ROOT MUTATIONS
# ============================================

class TiendasMutaciones(graphene.ObjectType):
    crear_tienda = CrearTienda.Field()
    editar_tienda = EditarTienda.Field()
    eliminar_tienda = EliminarTienda.Field()
    eliminar_foto_perfil = EliminarFotoPerfil.Field()
    eliminar_codigo_qr = EliminarCodigoQR.Field()
