from django.db import models
class Estado(models.Model):
    # Estados predefinidos
    ACTIVO = 'activo'
    INACTIVO = 'inactivo'
    SUSPENDIDO = 'suspendido'
    BLOQUEADO = 'bloqueado'
    PENDIENTE = 'pendiente'
    COMPLETADO = 'completado'
    RECHAZADO = 'rechazado'
    CANCELADO = 'cancelado'
    DISPONIBLE = 'disponible'
    VENDIDO = 'vendido'
    RESERVADO = 'reservado'
    
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    es_activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'estado'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
    
    def __str__(self):
        return self.nombre
    
    # Helpers existentes...
    @classmethod
    def get_activo(cls):
        return cls.objects.get(nombre=cls.ACTIVO)
    
    @classmethod
    def get_inactivo(cls):
        return cls.objects.get(nombre=cls.INACTIVO)
    
    @classmethod
    def get_suspendido(cls):
        return cls.objects.get(nombre=cls.SUSPENDIDO)
    
    @classmethod
    def get_bloqueado(cls):
        return cls.objects.get(nombre=cls.BLOQUEADO)
    
    # Nuevos helpers para ventas
    @classmethod
    def get_pendiente(cls):
        return cls.objects.get(nombre=cls.PENDIENTE)
    
    @classmethod
    def get_completado(cls):
        return cls.objects.get(nombre=cls.COMPLETADO)
    
    @classmethod
    def get_rechazado(cls):
        return cls.objects.get(nombre=cls.RECHAZADO)
    
    @classmethod
    def get_cancelado(cls):
        return cls.objects.get(nombre=cls.CANCELADO)
    
    # Helpers para productos
    @classmethod
    def get_disponible(cls):
        return cls.objects.get(nombre=cls.DISPONIBLE)
    
    @classmethod
    def get_vendido(cls):
        return cls.objects.get(nombre=cls.VENDIDO)
    
    @classmethod
    def get_reservado(cls):
        return cls.objects.get(nombre=cls.RESERVADO)