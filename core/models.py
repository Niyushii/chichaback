from django.db import models
class Estado(models.Model):
    """
    Tabla de estados del sistema - permite extensibilidad futura
    """
    # Estados predefinidos como constantes de clase
    ACTIVO = 'activo'
    INACTIVO = 'inactivo'
    SUSPENDIDO = 'suspendido'
    BLOQUEADO = 'bloqueado'
    
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    es_activo = models.BooleanField(default=True)  # Para saber si permite acciones
        
    class Meta:
        db_table = 'estado'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
    
    def __str__(self):
        return self.nombre
    
    @classmethod
    def get_activo(cls):
        """Helper para obtener estado activo (crea si no existe)"""
        estado, created = cls.objects.get_or_create(
            nombre=cls.ACTIVO,
            defaults={'descripcion': 'Usuario activo en el sistema', 'es_activo': True}
        )
        return estado
    
    @classmethod
    def get_inactivo(cls):
        """Helper para obtener estado inactivo (crea si no existe)"""
        estado, created = cls.objects.get_or_create(
            nombre=cls.INACTIVO,
            defaults={'descripcion': 'Usuario inactivo/eliminado', 'es_activo': False}
        )
        return estado
    
    @classmethod
    def get_suspendido(cls):
        """Helper para obtener estado suspendido (crea si no existe)"""
        estado, created = cls.objects.get_or_create(
            nombre=cls.SUSPENDIDO,
            defaults={'descripcion': 'Usuario suspendido temporalmente', 'es_activo': False}
        )
        return estado
    
    @classmethod
    def get_bloqueado(cls):
        """Helper para obtener estado bloqueado (crea si no existe)"""
        estado, created = cls.objects.get_or_create(
            nombre=cls.BLOQUEADO,
            defaults={'descripcion': 'Usuario bloqueado permanentemente', 'es_activo': False}
        )
        return estado