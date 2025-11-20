from django.db import migrations

def crear_estados(apps, schema_editor):
    Estado = apps.get_model('core', 'Estado')
    
    estados = [
        # Estados de usuario/tienda/general
        {'nombre': 'activo', 'descripcion': 'Registro activo en el sistema', 'es_activo': True},
        {'nombre': 'inactivo', 'descripcion': 'Registro inactivo/eliminado', 'es_activo': False},
        {'nombre': 'suspendido', 'descripcion': 'Usuario/Tienda suspendido temporalmente', 'es_activo': False},
        {'nombre': 'bloqueado', 'descripcion': 'Usuario/Tienda bloqueado permanentemente', 'es_activo': False},
        
        # Estados de venta
        {'nombre': 'pendiente', 'descripcion': 'Venta pendiente de confirmación', 'es_activo': True},
        {'nombre': 'completado', 'descripcion': 'Venta completada exitosamente', 'es_activo': True},
        {'nombre': 'rechazado', 'descripcion': 'Venta rechazada por el vendedor', 'es_activo': False},
        {'nombre': 'cancelado', 'descripcion': 'Venta cancelada por el comprador', 'es_activo': False},
        
        # Estados de producto
        {'nombre': 'disponible', 'descripcion': 'Producto disponible para venta', 'es_activo': True},
        {'nombre': 'vendido', 'descripcion': 'Producto ya vendido', 'es_activo': False},
        {'nombre': 'reservado', 'descripcion': 'Producto reservado (pago pendiente)', 'es_activo': True},
    ]
    
    for estado_data in estados:
        Estado.objects.get_or_create(
            nombre=estado_data['nombre'],
            defaults={
                'descripcion': estado_data['descripcion'],
                'es_activo': estado_data['es_activo']
            }
        )

def eliminar_estados(apps, schema_editor):
    Estado = apps.get_model('core', 'Estado')
    Estado.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),  # Ajusta al número de tu última migración
    ]

    operations = [
        migrations.RunPython(crear_estados, eliminar_estados),
    ]