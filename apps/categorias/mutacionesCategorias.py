import graphene
from graphql import GraphQLError
from django.utils import timezone
from .models import Categoria
from .categoriaType import CategoriaType
from apps.usuarios.utils import requiere_autenticacion
from core.models import Estado

# ============= INPUT TYPES =============
class CrearCategoriaInput(graphene.InputObjectType):
    nombre = graphene.String(required=True)
    icono = graphene.String()
    categoria_padre_id = graphene.ID()

class EditarCategoriaInput(graphene.InputObjectType):
    nombre = graphene.String()
    icono = graphene.String()
    categoria_padre_id = graphene.ID()

# ============= MUTATIONS =============
class CrearCategoria(graphene.Mutation):
    class Arguments:
        input = CrearCategoriaInput(required=True)
    
    categoria = graphene.Field(CategoriaType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def mutate(self, info, input, **kwargs):
        # Verificar que el nombre no esté duplicado
        if Categoria.objects.filter(
            nombre__iexact=input.nombre,
            fecha_eliminacion__isnull=True
        ).exists():
            raise GraphQLError("Ya existe una categoría con ese nombre")
        
        # Validar categoría padre si se proporciona
        categoria_padre = None
        if input.categoria_padre_id:
            try:
                categoria_padre = Categoria.objects.get(
                    pk=input.categoria_padre_id,
                    fecha_eliminacion__isnull=True
                )
            except Categoria.DoesNotExist:
                raise GraphQLError("La categoría padre no existe")
        
        # Crear categoría
        categoria = Categoria(
            nombre=input.nombre,
            icono=input.icono if input.icono else None,
            categoria_padre=categoria_padre,
            estado=Estado.get_activo()
        )
        categoria.save()
        
        return CrearCategoria(
            categoria=categoria,
            mensaje="Categoría creada exitosamente"
        )

class EditarCategoria(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = EditarCategoriaInput(required=True)
    
    categoria = graphene.Field(CategoriaType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def mutate(self, info, id, input, **kwargs):
        try:
            categoria = Categoria.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Categoria.DoesNotExist:
            raise GraphQLError("Categoría no encontrada")
        
        # Actualizar nombre si se proporciona
        if input.nombre:
            # Verificar duplicados (excluyendo la actual)
            if Categoria.objects.filter(
                nombre__iexact=input.nombre,
                fecha_eliminacion__isnull=True
            ).exclude(pk=id).exists():
                raise GraphQLError("Ya existe otra categoría con ese nombre")
            categoria.nombre = input.nombre
        
        # Actualizar ícono si se proporciona
        if input.icono is not None:
            categoria.icono = input.icono
        
        # Actualizar categoría padre si se proporciona
        if input.categoria_padre_id is not None:
            if input.categoria_padre_id:
                try:
                    categoria_padre = Categoria.objects.get(
                        pk=input.categoria_padre_id,
                        fecha_eliminacion__isnull=True
                    )
                    
                    # Validar que no se cree un ciclo (la categoría padre no puede ser descendiente)
                    if categoria_padre.id == categoria.id:
                        raise GraphQLError("Una categoría no puede ser su propia categoría padre")
                    
                    # Verificar recursivamente que no haya ciclos
                    temp_padre = categoria_padre
                    while temp_padre:
                        if temp_padre.categoria_padre and temp_padre.categoria_padre.id == categoria.id:
                            raise GraphQLError("No se puede crear un ciclo en la jerarquía de categorías")
                        temp_padre = temp_padre.categoria_padre
                    
                    categoria.categoria_padre = categoria_padre
                except Categoria.DoesNotExist:
                    raise GraphQLError("La categoría padre no existe")
            else:
                categoria.categoria_padre = None
        
        categoria.save()
        
        return EditarCategoria(
            categoria=categoria,
            mensaje="Categoría actualizada exitosamente"
        )

class EliminarCategoria(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    ok = graphene.Boolean()
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def mutate(self, info, id, **kwargs):
        try:
            categoria = Categoria.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Categoria.DoesNotExist:
            raise GraphQLError("Categoría no encontrada")
        
        # Verificar si tiene subcategorías activas
        if categoria.subcategorias.filter(fecha_eliminacion__isnull=True).exists():
            raise GraphQLError(
                "No se puede eliminar una categoría que tiene subcategorías activas. "
                "Elimina primero las subcategorías o reasígnalas."
            )
        
        # Verificar si tiene productos asociados
        if categoria.productos.filter(fecha_eliminacion__isnull=True).exists():
            raise GraphQLError(
                "No se puede eliminar una categoría que tiene productos asociados. "
                "Reasigna los productos a otra categoría primero."
            )
        
        # Soft delete
        categoria.fecha_eliminacion = timezone.now()
        categoria.estado = Estado.get_inactivo()
        categoria.save()
        
        return EliminarCategoria(
            ok=True,
            mensaje="Categoría eliminada exitosamente"
        )

# ============= MUTATION CLASS =============
class CategoriasMutaciones(graphene.ObjectType):
    crear_categoria = CrearCategoria.Field()
    editar_categoria = EditarCategoria.Field()
    eliminar_categoria = EliminarCategoria.Field()