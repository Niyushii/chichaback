import graphene
from graphql import GraphQLError
from .categoriaType import CategoriaType
from .models import Categoria

class CategoriasQueries(graphene.ObjectType):
    # ============= QUERIES PÚBLICAS =============
    todas_categorias = graphene.List(
        CategoriaType,
        solo_activas=graphene.Boolean(default_value=True),
        solo_principales=graphene.Boolean(default_value=False),
        description="Lista todas las categorías del sistema"
    )
    
    categoria_por_id = graphene.Field(
        CategoriaType,
        id=graphene.ID(required=True),
        description="Obtiene una categoría por ID"
    )
    
    categorias_jerarquia = graphene.List(
        CategoriaType,
        description="Obtiene la jerarquía completa de categorías (solo categorías principales con sus subcategorías)"
    )
    
    subcategorias_de = graphene.List(
        CategoriaType,
        categoria_id=graphene.ID(required=True),
        description="Obtiene las subcategorías de una categoría específica"
    )
    
    buscar_categorias = graphene.List(
        CategoriaType,
        busqueda=graphene.String(required=True),
        description="Busca categorías por nombre"
    )
    
    # ============= RESOLVERS =============
    
    def resolve_todas_categorias(self, info, solo_activas=True, solo_principales=False):
        """Lista todas las categorías con filtros opcionales"""
        queryset = Categoria.objects.all()
        
        if solo_activas:
            queryset = queryset.filter(fecha_eliminacion__isnull=True)
        
        if solo_principales:
            queryset = queryset.filter(categoria_padre__isnull=True)
        
        return queryset.select_related('categoria_padre', 'estado').order_by('nombre')
    
    def resolve_categoria_por_id(self, info, id):
        """Obtiene una categoría específica por ID"""
        try:
            return Categoria.objects.select_related(
                'categoria_padre', 
                'estado'
            ).get(pk=id)
        except Categoria.DoesNotExist:
            raise GraphQLError("Categoría no encontrada")
    
    def resolve_categorias_jerarquia(self, info):
        """
        Retorna solo las categorías principales (sin padre).
        Las subcategorías se pueden acceder mediante el campo 'subcategorias' 
        en cada CategoriaType gracias a la relación en el modelo.
        """
        return Categoria.objects.filter(
            categoria_padre__isnull=True,
            fecha_eliminacion__isnull=True
        ).select_related('estado').prefetch_related('subcategorias').order_by('nombre')
    
    def resolve_subcategorias_de(self, info, categoria_id):
        """Obtiene las subcategorías de una categoría específica"""
        try:
            categoria = Categoria.objects.get(
                pk=categoria_id,
                fecha_eliminacion__isnull=True
            )
        except Categoria.DoesNotExist:
            raise GraphQLError("Categoría no encontrada")
        
        return categoria.subcategorias.filter(
            fecha_eliminacion__isnull=True
        ).select_related('estado').order_by('nombre')
    
    def resolve_buscar_categorias(self, info, busqueda):
        """Busca categorías por nombre"""
        return Categoria.objects.filter(
            nombre__icontains=busqueda,
            fecha_eliminacion__isnull=True
        ).select_related('categoria_padre', 'estado').order_by('nombre')