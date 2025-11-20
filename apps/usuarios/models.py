from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from core.models import Estado

class Usuario(models.Model):
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    celular = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.URLField(max_length=500, blank=True, null=True)
    is_seller = models.BooleanField(default=False)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='usuarios')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]
    
    def __str__(self):
        return f"{self.nombre} {self.apellidos} (@{self.username})"
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class Moderador(models.Model):
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    celular = models.CharField(max_length=20, blank=True, null=True)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='administradores')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'administrador'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'
    
    def __str__(self):
        return f"{self.nombre} {self.apellidos} - Admin"
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class SuperAdministrador(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='superadministradores')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_eliminacion = models.DateTimeField(blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'superadministrador'
        verbose_name = 'Super Administrador'
        verbose_name_plural = 'Super Administradores'
    
    def __str__(self):
        return f"SuperAdmin - {self.username}"
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
# Nuevo modelo para auditoría de moderadores
class Auditoria(models.Model):
    usuario_tipo = models.CharField(max_length=20, blank=True, null=True)
    usuario_id = models.IntegerField(blank=True, null=True)
    usuario_email = models.EmailField(max_length=255, blank=True, null=True)

    accion = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auditoria'
        ordering = ['-fecha']
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditorías'
        indexes = [
            models.Index(fields=['usuario_tipo', 'usuario_id']),
            models.Index(fields=['fecha']),
        ]

    @staticmethod
    def registrar(usuario, accion, descripcion, usuario_tipo=None):
        """
        Registra una acción de auditoría.
        
        Args:
            usuario: Instancia del usuario (Moderador o SuperAdmin)
            accion: String describiendo la acción
            descripcion: Descripción detallada
            usuario_tipo: 'moderador' o 'superadmin' (explícito)
        """
        # Si no se pasa usuario_tipo, intentar deducirlo
        if not usuario_tipo and usuario:
            class_name = usuario.__class__.__name__.lower()
            usuario_tipo = 'superadmin' if class_name == 'superadministrador' else class_name
        
        Auditoria.objects.create(
            usuario_tipo=usuario_tipo,
            usuario_id=usuario.id if usuario else None,
            usuario_email=usuario.email if usuario and hasattr(usuario, "email") else None,
            accion=accion,
            descripcion=descripcion
        )

    def __str__(self):
        return f"[{self.usuario_tipo}] {self.accion} - {self.fecha}"
