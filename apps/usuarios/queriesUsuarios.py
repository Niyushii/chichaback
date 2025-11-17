# apps/usuarios/queries.py
import graphene
from graphql import GraphQLError
from .usuariosType import UsuarioType, ModeradorType, SuperAdministradorType, AuditoriaType
from .models import Usuario, Moderador, SuperAdministrador, Auditoria
from .utils import requiere_autenticacion
from core.models import Estado

class UsuariosQueries(graphene.ObjectType):
    # ============= QUERIES PÚBLICAS (sin autenticación) =============
    verificar_email_disponible = graphene.Boolean(
        email=graphene.String(required=True),
        description="Verifica si un email está disponible para registro"
    )
    verificar_username_disponible = graphene.Boolean(
        username=graphene.String(required=True),
        description="Verifica si un username está disponible para registro"
    )
    
    # ============= QUERIES AUTENTICADAS - USUARIO =============
    mi_perfil = graphene.Field(
        UsuarioType,
        description="Obtiene el perfil del usuario autenticado"
    )
    
    # ============= QUERIES AUTENTICADAS - MODERADOR =============
    todos_usuarios = graphene.List(
        UsuarioType,
        solo_activos=graphene.Boolean(default_value=True),
        es_vendedor=graphene.Boolean(),
        buscar=graphene.String(),
        description="Lista todos los usuarios (requiere moderador o superadmin)"
    )
    usuario_por_id = graphene.Field(
        UsuarioType,
        id=graphene.ID(required=True),
        description="Obtiene un usuario por ID (requiere moderador o superadmin)"
    )
    
    # ============= QUERIES AUTENTICADAS - SUPERADMIN =============
    todos_moderadores = graphene.List(
        ModeradorType,
        solo_activos=graphene.Boolean(default_value=True),
        description="Lista todos los moderadores (requiere superadmin)"
    )
    moderador_por_id = graphene.Field(
        ModeradorType,
        id=graphene.ID(required=True),
        description="Obtiene un moderador por ID (requiere superadmin)"
    )
    superadmin_existe = graphene.Boolean(
        description="Verifica si ya existe un superadmin en el sistema"
    )
    
    # ============= ESTADÍSTICAS (SUPERADMIN/MODERADOR) =============
    estadisticas_usuarios = graphene.Field(
        'apps.usuarios.usuariosType.EstadisticasUsuariosType',
        description="Obtiene estadísticas generales de usuarios"
    )
    
    # ============ AUDITORÍA (SUPERADMIN) =============
    auditoria = graphene.List(AuditoriaType)
    
    # ============================================================
    # RESOLVERS - QUERIES PÚBLICAS
    # ============================================================
    
    def resolve_verificar_email_disponible(self, info, email):
        """Verifica si el email está disponible en los 3 modelos"""
        email_en_usuario = Usuario.objects.filter(email=email).exists()
        email_en_moderador = Moderador.objects.filter(email=email).exists()
        email_en_superadmin = SuperAdministrador.objects.filter(email=email).exists()
        
        return not (email_en_usuario or email_en_moderador or email_en_superadmin)
    
    def resolve_verificar_username_disponible(self, info, username):
        """Verifica si el username está disponible en los 3 modelos"""
        username_en_usuario = Usuario.objects.filter(username=username).exists()
        username_en_moderador = Moderador.objects.filter(username=username).exists()
        username_en_superadmin = SuperAdministrador.objects.filter(username=username).exists()
        
        return not (username_en_usuario or username_en_moderador or username_en_superadmin)
    
    def resolve_superadmin_existe(self, info):
        """Verifica si existe un superadmin activo (útil para UI de registro)"""
        return SuperAdministrador.objects.filter(fecha_eliminacion__isnull=True).exists()
    
    # ============================================================
    # RESOLVERS - USUARIO
    # ============================================================
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_mi_perfil(self, info, **kwargs):
        """Retorna el perfil completo del usuario autenticado"""
        return kwargs['current_user']
    
    # ============================================================
    # RESOLVERS - MODERADOR/SUPERADMIN
    # ============================================================
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def resolve_todos_usuarios(self, info, solo_activos=True, es_vendedor=None, buscar=None, **kwargs):
        """
        Lista usuarios con filtros opcionales
        - solo_activos: filtra por usuarios no eliminados
        - es_vendedor: filtra por tipo de usuario (vendedor o no)
        - buscar: busca por nombre, apellidos, email o username
        """
        queryset = Usuario.objects.all()
        
        # Filtro: solo activos
        if solo_activos:
            queryset = queryset.filter(fecha_eliminacion__isnull=True)
        
        # Filtro: es vendedor
        if es_vendedor is not None:
            queryset = queryset.filter(is_seller=es_vendedor)
        
        # Filtro: búsqueda
        if buscar:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) |
                Q(apellidos__icontains=buscar) |
                Q(email__icontains=buscar) |
                Q(username__icontains=buscar)
            )
        
        return queryset.select_related('estado').order_by('-fecha_creacion')
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def resolve_usuario_por_id(self, info, id, **kwargs):
        """Obtiene un usuario específico por ID"""
        try:
            return Usuario.objects.select_related('estado').get(pk=id)
        except Usuario.DoesNotExist:
            raise GraphQLError("Usuario no encontrado")
    
    # ============================================================
    # RESOLVERS - SOLO SUPERADMIN
    # ============================================================
    
    @requiere_autenticacion(user_types=['superadmin'])
    def resolve_todos_moderadores(self, info, solo_activos=True, **kwargs):
        """Lista moderadores (solo superadmin)"""
        queryset = Moderador.objects.all()
        
        if solo_activos:
            queryset = queryset.filter(fecha_eliminacion__isnull=True)
        
        return queryset.select_related('estado').order_by('-fecha_creacion')
    
    @requiere_autenticacion(user_types=['superadmin'])
    def resolve_moderador_por_id(self, info, id, **kwargs):
        """Obtiene un moderador específico por ID"""
        try:
            return Moderador.objects.select_related('estado').get(pk=id)
        except Moderador.DoesNotExist:
            raise GraphQLError("Moderador no encontrado")
    
    # Registro de auditoría
    @requiere_autenticacion(user_types=['superadmin'])
    def resolve_auditoria(self, info, **kwargs):
        return Auditoria.objects.all()
    
    # ============================================================
    # RESOLVERS - ESTADÍSTICAS
    # ============================================================
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def resolve_estadisticas_usuarios(self, info, **kwargs):
        """Retorna estadísticas generales de usuarios"""
        from .usuariosType import EstadisticasUsuariosType
        
        total_usuarios = Usuario.objects.count()
        usuarios_activos = Usuario.objects.filter(
            fecha_eliminacion__isnull=True,
            estado__nombre=Estado.ACTIVO
        ).count()
        usuarios_inactivos = Usuario.objects.filter(
            estado__nombre=Estado.INACTIVO
        ).count()
        vendedores = Usuario.objects.filter(
            is_seller=True,
            fecha_eliminacion__isnull=True
        ).count()
        
        # Usuarios registrados en los últimos 30 días
        from django.utils import timezone
        from datetime import timedelta
        hace_30_dias = timezone.now() - timedelta(days=30)
        nuevos_usuarios = Usuario.objects.filter(
            fecha_creacion__gte=hace_30_dias
        ).count()
        
        return EstadisticasUsuariosType(
            total=total_usuarios,
            activos=usuarios_activos,
            inactivos=usuarios_inactivos,
            vendedores=vendedores,
            nuevos_ultimos_30_dias=nuevos_usuarios
        )