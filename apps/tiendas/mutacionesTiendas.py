import graphene
import cloudinary.uploader
from graphql import GraphQLError
from django.utils import timezone
from .models import Tienda
from .tiendasType import TiendaType
from apps.usuarios.utils import requiere_autenticacion
from apps.usuarios.models import Usuario, Auditoria
from core.models import Estado
from core.graphql_scalars import Upload


# ============================================
# INPUT TYPES (SIN ARCHIVOS)
# ============================================

class CrearTiendaInput(graphene.InputObjectType):
    nombre = graphene.String(required=True)
    descripcion = graphene.String()
    telefono = graphene.String()
    direccion = graphene.String()


class EditarTiendaInput(graphene.InputObjectType):
    nombre = graphene.String()
    descripcion = graphene.String()
    telefono = graphene.String()
    direccion = graphene.String()


# ============================================
# MUTACIÓN: CREAR TIENDA
# ============================================

class CrearTienda(graphene.Mutation):
    class Arguments:
        input = CrearTiendaInput(required=True)
        foto_perfil = Upload()
        codigo_qr = Upload()

    tienda = graphene.Field(TiendaType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, foto_perfil=None, codigo_qr=None, **kwargs):
        usuario = kwargs['current_user']

        # Verificación de nombre único
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

        # --- SUBIR A CLOUDINARY SI HAY ARCHIVOS ---
        if foto_perfil:
            res = cloudinary.uploader.upload(
                foto_perfil,
                folder="tiendas/foto_perfil/"
            )
            tienda.foto_perfil = res["secure_url"]

        if codigo_qr:
            res = cloudinary.uploader.upload(
                codigo_qr,
                folder="tiendas/codigo_qr/"
            )
            tienda.codigo_qr = res["secure_url"]

        tienda.save()

        # Convertir en vendedor
        if not usuario.is_seller:
            usuario.is_seller = True
            usuario.save()

        return CrearTienda(
            tienda=tienda,
            mensaje=f"Tienda '{tienda.nombre}' creada exitosamente."
        )


# ============================================
# MUTACIÓN: EDITAR TIENDA
# ============================================

class EditarTienda(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = EditarTiendaInput(required=True)
        foto_perfil = Upload()
        codigo_qr = Upload()

    tienda = graphene.Field(TiendaType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario','moderador','superadmin'])
    def mutate(self, info, id, input, foto_perfil=None, codigo_qr=None, **kwargs):
        usuario = kwargs["current_user"]
        rol = kwargs["user_type"]

        try:
            tienda = Tienda.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        if rol == "usuario" and tienda.propietario.id != usuario.id:
            raise GraphQLError("No tienes permiso para editar esta tienda")

        # actualizar campos simples
        for field in ["nombre", "descripcion", "telefono", "direccion"]:
            value = getattr(input, field)
            if value is not None:
                setattr(tienda, field, value)

        # SUBIR NUEVAS IMÁGENES
        if foto_perfil:
            res = cloudinary.uploader.upload(
                foto_perfil,
                folder="tiendas/foto_perfil/"
            )
            tienda.foto_perfil = res["secure_url"]

        if codigo_qr:
            res = cloudinary.uploader.upload(
                codigo_qr,
                folder="tiendas/codigo_qr/"
            )
            tienda.codigo_qr = res["secure_url"]

        tienda.save()

        return EditarTienda(tienda=tienda, mensaje="Tienda actualizada exitosamente")



# ============================================
# MUTACIÓN: ELIMINAR TIENDA
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

        # ✅ Auditoría
        if rol in ["moderador", "superadmin"]:
            if kwargs['user_type'] in ['moderador', 'superadmin']:
                Auditoria.registrar(
                    usuario=usuario,
                    accion="eliminar_tienda",
                    descripcion=f"{rol.capitalize()} {usuario.email} eliminó la tienda '{tienda.nombre}'"
                )

        # Verificar productos activos
        if tienda.productos.filter(fecha_eliminacion__isnull=True).exists():
            raise GraphQLError("No se puede eliminar una tienda con productos activos")

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

        # ✅ Auditoría
        if rol in ["moderador", "superadmin"]:
            if kwargs['user_type'] in ['moderador', 'superadmin']:
                Auditoria.registrar(
                    usuario=usuario,
                    accion="eliminar_foto_perfil_tienda",
                    descripcion=f"{rol.capitalize()} {usuario.email} eliminó foto de perfil de '{tienda.nombre}'"
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

        # ✅ Auditoría
        if rol in ["moderador", "superadmin"]:
            if kwargs['user_type'] in ['moderador', 'superadmin']:
                Auditoria.registrar(
                    usuario=usuario,
                    accion="eliminar_codigo_qr_tienda",
                    descripcion=f"{rol.capitalize()} {usuario.email} eliminó código QR de '{tienda.nombre}'"
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