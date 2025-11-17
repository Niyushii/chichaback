import graphene
from graphql import GraphQLError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Usuario, Moderador, SuperAdministrador
from .usuariosType import UsuarioType, ModeradorType, SuperAdministradorType
from .utils import crear_token, requiere_autenticacion
from core.models import Estado

# ============= INPUT TYPES =============
class RegistroUsuarioInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    username = graphene.String(required=True)
    password = graphene.String(required=True)
    nombre = graphene.String(required=True)
    apellidos = graphene.String(required=True)
    celular = graphene.String()

class LoginInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    password = graphene.String(required=True)

class EditarUsuarioInput(graphene.InputObjectType):
    nombre = graphene.String()
    apellidos = graphene.String()
    celular = graphene.String()
    foto_perfil = graphene.String()
    is_seller = graphene.Boolean()

class CrearModeradorInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    username = graphene.String(required=True)
    password = graphene.String(required=True)
    nombre = graphene.String(required=True)
    apellidos = graphene.String(required=True)
    celular = graphene.String()

class EditarModeradorInput(graphene.InputObjectType):
    nombre = graphene.String()
    apellidos = graphene.String()
    celular = graphene.String()

# ============= SUPER ADMIN MUTATIONS =============
class RegistrarSuperAdmin(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    superadmin = graphene.Field(SuperAdministradorType)
    token = graphene.String()
    mensaje = graphene.String()
    
    def mutate(self, info, username, email, password):
        # Verificar que no exista otro SuperAdmin activo
        if SuperAdministrador.objects.filter(fecha_eliminacion__isnull=True).exists():
            raise GraphQLError("Ya existe un Super Administrador registrado en el sistema")
        
        # Validar email
        try:
            validate_email(email)
        except ValidationError:
            raise GraphQLError("Email inválido")
        
        # Validar longitud de password
        if len(password) < 8:
            raise GraphQLError("La contraseña debe tener al menos 8 caracteres")
        
        # Crear SuperAdmin usando el helper de Estado
        superadmin = SuperAdministrador(
            username=username,
            email=email,
            estado=Estado.get_activo()  # ✅ Usa el helper
        )
        superadmin.set_password(password)
        superadmin.save()
        
        # Generar token
        token = crear_token(superadmin.id, 'superadmin')
        
        return RegistrarSuperAdmin(
            superadmin=superadmin,
            token=token,
            mensaje="Super Administrador registrado exitosamente"
        )

class CrearModerador(graphene.Mutation):
    class Arguments:
        input = CrearModeradorInput(required=True)
    
    moderador = graphene.Field(ModeradorType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['superadmin'])
    def mutate(self, info, input, **kwargs):
        # Validar email
        try:
            validate_email(input.email)
        except ValidationError:
            raise GraphQLError("Email inválido")
        
        # Verificar duplicados
        if Moderador.objects.filter(email=input.email).exists():
            raise GraphQLError("El email ya está registrado")
        if Moderador.objects.filter(username=input.username).exists():
            raise GraphQLError("El username ya está en uso")
        
        # Validar longitud de password
        if len(input.password) < 8:
            raise GraphQLError("La contraseña debe tener al menos 8 caracteres")
        
        # Crear moderador usando el helper de Estado
        moderador = Moderador(
            email=input.email,
            username=input.username,
            nombre=input.nombre,
            apellidos=input.apellidos,
            celular=input.celular,
            estado=Estado.get_activo()  # ✅ Usa el helper
        )
        moderador.set_password(input.password)
        moderador.save()
        
        return CrearModerador(
            moderador=moderador,
            mensaje="Moderador creado exitosamente"
        )

class EditarModerador(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = EditarModeradorInput(required=True)
    
    moderador = graphene.Field(ModeradorType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['superadmin'])
    def mutate(self, info, id, input, **kwargs):
        try:
            moderador = Moderador.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Moderador.DoesNotExist:
            raise GraphQLError("Moderador no encontrado")
        
        # Actualizar campos proporcionados
        if input.nombre:
            moderador.nombre = input.nombre
        if input.apellidos:
            moderador.apellidos = input.apellidos
        if input.celular is not None:
            moderador.celular = input.celular
        
        moderador.save()
        
        return EditarModerador(
            moderador=moderador,
            mensaje="Moderador actualizado exitosamente"
        )

class EliminarModerador(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    ok = graphene.Boolean()
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['superadmin'])
    def mutate(self, info, id, **kwargs):
        try:
            moderador = Moderador.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Moderador.DoesNotExist:
            raise GraphQLError("Moderador no encontrado")
        
        # Soft delete
        moderador.fecha_eliminacion = timezone.now()
        moderador.estado = Estado.get_inactivo()  # ✅ Usa el helper
        moderador.save()
        
        return EliminarModerador(
            ok=True,
            mensaje="Moderador eliminado exitosamente"
        )

# ============= USUARIO MUTATIONS =============
class RegistrarUsuario(graphene.Mutation):
    class Arguments:
        input = RegistroUsuarioInput(required=True)
    
    usuario = graphene.Field(UsuarioType)
    token = graphene.String()
    mensaje = graphene.String()
    
    def mutate(self, info, input):
        # Validar email
        try:
            validate_email(input.email)
        except ValidationError:
            raise GraphQLError("Email inválido")
        
        # Verificar duplicados
        if Usuario.objects.filter(email=input.email).exists():
            raise GraphQLError("El email ya está registrado")
        if Usuario.objects.filter(username=input.username).exists():
            raise GraphQLError("El username ya está en uso")
        
        # Validar longitud de password
        if len(input.password) < 8:
            raise GraphQLError("La contraseña debe tener al menos 8 caracteres")
        
        # Crear usuario usando el helper de Estado
        usuario = Usuario(
            email=input.email,
            username=input.username,
            nombre=input.nombre,
            apellidos=input.apellidos,
            celular=input.celular,
            estado=Estado.get_activo()  # ✅ Usa el helper
        )
        usuario.set_password(input.password)
        usuario.save()
        
        # Generar token
        token = crear_token(usuario.id, 'usuario')
        
        return RegistrarUsuario(
            usuario=usuario,
            token=token,
            mensaje="Usuario registrado exitosamente"
        )

class Login(graphene.Mutation):
    class Arguments:
        input = LoginInput(required=True)
    
    token = graphene.String()
    user_type = graphene.String()
    user_id = graphene.ID()
    usuario = graphene.Field(UsuarioType)
    moderador = graphene.Field(ModeradorType)
    superadmin = graphene.Field(SuperAdministradorType)
    mensaje = graphene.String()
    
    def mutate(self, info, input):
        email = input.email
        password = input.password
        
        # Buscar en Usuario
        try:
            usuario = Usuario.objects.get(email=email, fecha_eliminacion__isnull=True)
            # Verificar que el usuario esté activo
            if usuario.estado.nombre != Estado.ACTIVO:
                raise GraphQLError("Tu cuenta está inactiva. Contacta al administrador")
            
            if usuario.check_password(password):
                token = crear_token(usuario.id, 'usuario')
                return Login(
                    token=token,
                    user_type='usuario',
                    user_id=usuario.id,
                    usuario=usuario,
                    mensaje="Login exitoso"
                )
        except Usuario.DoesNotExist:
            pass
        
        # Buscar en Moderador
        try:
            moderador = Moderador.objects.get(email=email, fecha_eliminacion__isnull=True)
            # Verificar que el moderador esté activo
            if moderador.estado.nombre != Estado.ACTIVO:
                raise GraphQLError("Tu cuenta está inactiva. Contacta al Super Administrador")
            
            if moderador.check_password(password):
                token = crear_token(moderador.id, 'moderador')
                return Login(
                    token=token,
                    user_type='moderador',
                    user_id=moderador.id,
                    moderador=moderador,
                    mensaje="Login exitoso"
                )
        except Moderador.DoesNotExist:
            pass
        
        # Buscar en SuperAdmin
        try:
            superadmin = SuperAdministrador.objects.get(email=email, fecha_eliminacion__isnull=True)
            # Verificar que el superadmin esté activo
            if superadmin.estado.nombre != Estado.ACTIVO:
                raise GraphQLError("Tu cuenta está inactiva")
            
            if superadmin.check_password(password):
                token = crear_token(superadmin.id, 'superadmin')
                return Login(
                    token=token,
                    user_type='superadmin',
                    user_id=superadmin.id,
                    superadmin=superadmin,
                    mensaje="Login exitoso"
                )
        except SuperAdministrador.DoesNotExist:
            pass
        
        raise GraphQLError("Credenciales inválidas")

class EditarUsuario(graphene.Mutation):
    class Arguments:
        input = EditarUsuarioInput(required=True)
    
    usuario = graphene.Field(UsuarioType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, **kwargs):
        usuario = kwargs['current_user']
        
        # Actualizar campos proporcionados
        if input.nombre:
            usuario.nombre = input.nombre
        if input.apellidos:
            usuario.apellidos = input.apellidos
        if input.celular is not None:
            usuario.celular = input.celular
        if input.foto_perfil is not None:
            usuario.foto_perfil = input.foto_perfil
        if input.is_seller is not None:
            usuario.is_seller = input.is_seller
        
        usuario.save()
        
        return EditarUsuario(
            usuario=usuario,
            mensaje="Perfil actualizado exitosamente"
        )

class EliminarUsuario(graphene.Mutation):
    ok = graphene.Boolean()
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, **kwargs):
        usuario = kwargs['current_user']
        
        # Soft delete
        usuario.fecha_eliminacion = timezone.now()
        usuario.estado = Estado.get_inactivo()  # ✅ Usa el helper
        usuario.save()
        
        return EliminarUsuario(
            ok=True,
            mensaje="Cuenta eliminada exitosamente"
        )

# ============= MUTATION CLASS =============
class UsuariosMutaciones(graphene.ObjectType):
    # SuperAdmin
    registrar_superadmin = RegistrarSuperAdmin.Field()
    crear_moderador = CrearModerador.Field()
    editar_moderador = EditarModerador.Field()
    eliminar_moderador = EliminarModerador.Field()
    
    # Usuario
    registrar_usuario = RegistrarUsuario.Field()
    login = Login.Field()
    editar_usuario = EditarUsuario.Field()
    eliminar_usuario = EliminarUsuario.Field()