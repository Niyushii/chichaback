import graphene
from graphene_django import DjangoObjectType
from .models import Usuario, Moderador, SuperAdministrador, Auditoria, Notificacion, AuditoriaUsuario

class UsuarioType(DjangoObjectType):
    class Meta:
        model = Usuario
        fields = "__all__"
        description = "Representa un usuario registrado en el sistema."

class ModeradorType(DjangoObjectType):
    class Meta:
        model = Moderador
        fields = "__all__"
        description = "Representa un moderador con privilegios especiales."

class SuperAdministradorType(DjangoObjectType):
    class Meta:
        model = SuperAdministrador
        fields = "__all__"
        description = "Representa un superadministrador con control total sobre el sistema."
        
class EstadisticasUsuariosType(graphene.ObjectType):
    """Tipo para estadísticas de usuarios"""
    total = graphene.Int(description="Total de usuarios registrados")
    activos = graphene.Int(description="Usuarios activos")
    inactivos = graphene.Int(description="Usuarios inactivos")
    vendedores = graphene.Int(description="Usuarios que son vendedores")
    nuevos_ultimos_30_dias = graphene.Int(description="Usuarios registrados en los últimos 30 días")
class EstadisticasModeradoresType(graphene.ObjectType):
    """Tipo para estadísticas de moderadores"""
    total = graphene.Int(description="Total de moderadores registrados")
    activos = graphene.Int(description="Moderadores activos")
    inactivos = graphene.Int(description="Moderadores inactivos")
    nuevos_ultimos_30_dias = graphene.Int(description="Moderadores registrados en los últimos 30 días")
    
class AuditoriaType(DjangoObjectType):
    class Meta:
        model = Auditoria
        fields = "__all__"
        description = "Representa un registro de auditoría de acciones realizadas por usuarios."
        
class AuditoriaUsuarioType(DjangoObjectType):
    class Meta:
        model = AuditoriaUsuario
        fields = "__all__"
        description = "Representa un registro de auditoría de acciones realizadas por usuarios normales o vendedores."        
        
class NotificacionType(DjangoObjectType):
    class Meta:
        model = Notificacion
        fields = "__all__"
        
class EstadisticasModeradoresType(graphene.ObjectType):
    total = graphene.Int()
    activos = graphene.Int()
    inactivos = graphene.Int()
    nuevos_ultimos_30_dias = graphene.Int()