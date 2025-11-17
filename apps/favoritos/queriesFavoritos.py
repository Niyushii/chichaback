import graphene
from graphql import GraphQLError
from .favoritosType import FavoritoType, EstadisticasFavoritosType
from .models import Favoritos
from apps.usuarios.utils import requiere_autenticacion

class FavoritosQueries(graphene.ObjectType):
    # ============= QUERIES AUTENTICADAS =============
    
    mis_favoritos = graphene.List(
        FavoritoType,
        description="Lista todos los productos favoritos del usuario autenticado"
    )
    
    es_favorito = graphene.Boolean(
        tienda_producto_id=graphene.ID(required=True),
        description="Verifica si un producto está en favoritos del usuario"
    )
    
    cantidad_favoritos = graphene.Int(
        description="Retorna la cantidad total de favoritos del usuario"
    )
    
    favoritos_por_tienda = graphene.List(
        FavoritoType,
        tienda_id=graphene.ID(required=True),
        description="Lista favoritos del usuario filtrados por tienda"
    )
    
    favoritos_por_categoria = graphene.List(
        FavoritoType,
        categoria_id=graphene.ID(required=True),
        description="Lista favoritos del usuario filtrados por categoría"
    )
    
    estadisticas_favoritos = graphene.Field(
        EstadisticasFavoritosType,
        description="Obtiene estadísticas de favoritos del usuario"
    )
    
    # ============================================================
    # RESOLVERS
    # ============================================================
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_mis_favoritos(self, info, **kwargs):
        """Lista todos los favoritos activos del usuario"""
        usuario = kwargs['current_user']
        
        return Favoritos.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True
        ).select_related(
            'tienda_producto__producto',
            'tienda_producto__tienda',
            'tienda_producto__talla',
            'estado'
        ).prefetch_related(
            'tienda_producto__imagenes'
        ).order_by('-fecha_creacion')
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_es_favorito(self, info, tienda_producto_id, **kwargs):
        """Verifica si un producto específico está en favoritos"""
        usuario = kwargs['current_user']
        
        return Favoritos.objects.filter(
            usuario=usuario,
            tienda_producto_id=tienda_producto_id,
            fecha_eliminacion__isnull=True
        ).exists()
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_cantidad_favoritos(self, info, **kwargs):
        """Retorna el conteo total de favoritos activos"""
        usuario = kwargs['current_user']
        
        return Favoritos.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True
        ).count()
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_favoritos_por_tienda(self, info, tienda_id, **kwargs):
        """Lista favoritos filtrados por una tienda específica"""
        usuario = kwargs['current_user']
        
        return Favoritos.objects.filter(
            usuario=usuario,
            tienda_producto__tienda_id=tienda_id,
            fecha_eliminacion__isnull=True
        ).select_related(
            'tienda_producto__producto',
            'tienda_producto__tienda',
            'tienda_producto__talla',
            'estado'
        ).order_by('-fecha_creacion')
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_favoritos_por_categoria(self, info, categoria_id, **kwargs):
        """Lista favoritos filtrados por categoría de producto"""
        usuario = kwargs['current_user']
        
        return Favoritos.objects.filter(
            usuario=usuario,
            tienda_producto__producto__categoria_id=categoria_id,
            fecha_eliminacion__isnull=True
        ).select_related(
            'tienda_producto__producto__categoria',
            'tienda_producto__producto',
            'tienda_producto__tienda',
            'estado'
        ).order_by('-fecha_creacion')
    
    @requiere_autenticacion(user_types=['usuario'])
    def resolve_estadisticas_favoritos(self, info, **kwargs):
        """Retorna estadísticas generales de favoritos del usuario"""
        usuario = kwargs['current_user']
        
        from django.db.models import Count, Avg, Min, Max
        from django.utils import timezone
        from datetime import timedelta
        
        # Total de favoritos activos
        total = Favoritos.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True
        ).count()
        
        # Favoritos agregados en los últimos 7 días
        hace_7_dias = timezone.now() - timedelta(days=7)
        recientes = Favoritos.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True,
            fecha_creacion__gte=hace_7_dias
        ).count()
        
        # Tienda con más productos en favoritos
        tienda_favorita = Favoritos.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True
        ).values(
            'tienda_producto__tienda__id',
            'tienda_producto__tienda__nombre'
        ).annotate(
            cantidad=Count('id')
        ).order_by('-cantidad').first()
        
        tienda_favorita_nombre = tienda_favorita['tienda_producto__tienda__nombre'] if tienda_favorita else None
        tienda_favorita_cantidad = tienda_favorita['cantidad'] if tienda_favorita else 0
        
        # Categoría con más productos en favoritos
        categoria_favorita = Favoritos.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True
        ).values(
            'tienda_producto__producto__categoria__id',
            'tienda_producto__producto__categoria__nombre'
        ).annotate(
            cantidad=Count('id')
        ).order_by('-cantidad').first()
        
        categoria_favorita_nombre = categoria_favorita['tienda_producto__producto__categoria__nombre'] if categoria_favorita else None
        categoria_favorita_cantidad = categoria_favorita['cantidad'] if categoria_favorita else 0
        
        # Precio promedio de favoritos
        precios = Favoritos.objects.filter(
            usuario=usuario,
            fecha_eliminacion__isnull=True
        ).aggregate(
            promedio=Avg('tienda_producto__precio'),
            minimo=Min('tienda_producto__precio'),
            maximo=Max('tienda_producto__precio')
        )
        
        return EstadisticasFavoritosType(
            total=total,
            recientes_7_dias=recientes,
            tienda_favorita=tienda_favorita_nombre,
            tienda_favorita_cantidad=tienda_favorita_cantidad,
            categoria_favorita=categoria_favorita_nombre,
            categoria_favorita_cantidad=categoria_favorita_cantidad,
            precio_promedio=float(precios['promedio']) if precios['promedio'] else 0.0,
            precio_minimo=float(precios['minimo']) if precios['minimo'] else 0.0,
            precio_maximo=float(precios['maximo']) if precios['maximo'] else 0.0
        )