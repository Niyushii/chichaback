import graphene
from graphql import GraphQLError
from core.graphql_scalars import Upload
from apps.usuarios.models import Auditoria
from apps.usuarios.usuariosType import AuditoriaType
from apps.usuarios.utils import requiere_autenticacion
from apps.tiendas.models import Tienda
from .models import Producto, TiendaProducto, ImagenProducto, Talla
from apps.categorias.models import Categoria
from core.models import Estado
from .productosType import TiendaProductoType, ImagenProductoType, TallaType, ProductoType, ImagenProductoType
from django.utils import timezone


class CrearProductoInput(graphene.InputObjectType):
    tienda_id = graphene.ID(required=True)
    nombre = graphene.String(required=True)
    descripcion = graphene.String()
    categoria_id = graphene.ID()
    talla_id = graphene.ID()
    precio = graphene.Float(required=True)
    stock = graphene.Int(required=True)
    imagenes = graphene.List(Upload)


class CrearProducto(graphene.Mutation):
    class Arguments:
        input = CrearProductoInput(required=True)

    producto_tienda = graphene.Field(lambda: TiendaProductoType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, **kwargs):
        usuario = kwargs["current_user"]

        # Validar tienda
        try:
            tienda = Tienda.objects.get(pk=input.tienda_id, fecha_eliminacion__isnull=True)
        except Tienda.DoesNotExist:
            raise GraphQLError("Tienda no encontrada")

        if tienda.propietario != usuario:
            raise GraphQLError("No puedes agregar productos a esta tienda")

        # Crear producto base si no existe
        producto = Producto.objects.create(
            nombre=input.nombre,
            descripcion=input.descripcion,
            categoria_id=input.categoria_id,
            estado=Estado.get_activo()
        )

        # Crear relación TiendaProducto
        tp = TiendaProducto.objects.create(
            tienda=tienda,
            producto=producto,
            talla_id=input.talla_id,
            descripcion=input.descripcion,
            precio=input.precio,
            stock=input.stock,
            estado=Estado.get_activo()
        )

        # Subir imágenes
        if input.imagenes:
            for img in input.imagenes:
                ImagenProducto.objects.create(
                    producto=tp,
                    archivo=img,
                    nombre=f"{producto.nombre}-{tp.id}",
                    estado=Estado.get_activo()
                )

        return CrearProducto(
            producto_tienda=tp,
            mensaje="Producto creado exitosamente"
        )

# Edición de productos
class EditarProductoInput(graphene.InputObjectType):
    tienda_producto_id = graphene.ID(required=True)
    nombre = graphene.String()
    descripcion = graphene.String()
    categoria_id = graphene.ID()
    talla_id = graphene.ID()
    precio = graphene.Float()
    stock = graphene.Int()


class EditarProducto(graphene.Mutation):
    class Arguments:
        input = EditarProductoInput(required=True)

    producto_tienda = graphene.Field(TiendaProductoType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, **kwargs):
        usuario = kwargs["current_user"]

        # Buscar relación tienda-producto
        try:
            tp = TiendaProducto.objects.get(
                pk=input.tienda_producto_id,
                fecha_eliminacion__isnull=True
            )
        except TiendaProducto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")

        # Validar propiedad
        if tp.tienda.propietario != usuario and not (usuario.es_admin or usuario.es_moderador):
            raise GraphQLError("No tienes permisos para editar este producto")

        # Editar producto base
        p = tp.producto
        if input.nombre:
            p.nombre = input.nombre
        if input.descripcion:
            p.descripcion = input.descripcion
        if input.categoria_id:
            p.categoria_id = input.categoria_id
        p.save()
        
        if usuario in ['moderador', 'superadmin']:
            from apps.usuarios.models import Auditoria
            Auditoria.registrar(
                usuario=usuario,
                accion="editar_producto",
                descripcion=f"{usuario.capitalize()} {usuario.email} editó producto '{tp.producto.nombre}'",
                usuario_tipo=usuario
    )
        # Editar variante (TiendaProducto)
        if input.talla_id:
            tp.talla_id = input.talla_id
        if input.precio is not None:
            tp.precio = input.precio
        if input.stock is not None:
            tp.stock = input.stock
        tp.save()

        return EditarProducto(
            producto_tienda=tp,
            mensaje="Producto actualizado correctamente"
        )

# Eliminación de productos
class EliminarProducto(graphene.Mutation):
    class Arguments:
        tienda_producto_id = graphene.ID(required=True)

    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, tienda_producto_id, **kwargs):
        usuario = kwargs["current_user"]

        try:
            tp = TiendaProducto.objects.get(
                pk=tienda_producto_id,
                fecha_eliminacion__isnull=True
            )
        except TiendaProducto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")

        if tp.tienda.propietario != usuario and not (usuario.es_admin or usuario.es_moderador):
            raise GraphQLError("No tienes permisos para eliminar este producto")

        # Soft delete
        tp.fecha_eliminacion = timezone.now()
        tp.save()

        # Soft delete imágenes
        tp.imagenes.update(fecha_eliminacion=timezone.now())
        if usuario in ['moderador', 'superadmin']:
            from apps.usuarios.models import Auditoria
            Auditoria.registrar(
                usuario=usuario,
                accion="eliminar_producto",
                descripcion=f"{usuario.capitalize()} {usuario.email} eliminó producto '{tp.producto.nombre}'",
                usuario_tipo=usuario
            )

        return EliminarProducto(mensaje="Producto eliminado correctamente")

# Subir Imagen del producto
class SubirImagenProducto(graphene.Mutation):
    class Arguments:
        tienda_producto_id = graphene.ID(required=True)
        imagen = Upload(required=True)

    imagen_obj = graphene.Field(ImagenProductoType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, tienda_producto_id, imagen, **kwargs):
        usuario = kwargs["current_user"]

        try:
            tp = TiendaProducto.objects.get(
                pk=tienda_producto_id,
                fecha_eliminacion__isnull=True
            )
        except TiendaProducto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")

        if tp.tienda.propietario != usuario and not (usuario.es_admin or usuario.es_moderador):
            raise GraphQLError("No autorizado")

        img = ImagenProducto.objects.create(
            producto=tp,
            archivo=imagen,
            nombre=f"prod-{tp.id}",
            estado=Estado.get_activo()
        )

        return SubirImagenProducto(
            imagen_obj=img,
            mensaje="Imagen subida correctamente"
        )

# Eliminar Imagen del producto
class EliminarImagenProducto(graphene.Mutation):
    class Arguments:
        imagen_id = graphene.ID(required=True)

    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, imagen_id, **kwargs):
        usuario = kwargs["current_user"]

        try:
            img = ImagenProducto.objects.get(
                pk=imagen_id,
                fecha_eliminacion__isnull=True
            )
        except ImagenProducto.DoesNotExist:
            raise GraphQLError("Imagen no encontrada")

        if img.producto.tienda.propietario != usuario and not (usuario.es_admin or usuario.es_moderador):
            raise GraphQLError("No autorizado")

        img.fecha_eliminacion = timezone.now()
        img.save()

        return EliminarImagenProducto(mensaje="Imagen eliminada correctamente")

#Editar imagen
class EditarImagenProductoInput(graphene.InputObjectType):
    imagen_id = graphene.ID(required=True)
    nombre = graphene.String()
    descripcion = graphene.String()
    archivo = Upload()


class EditarImagenProducto(graphene.Mutation):
    class Arguments:
        input = EditarImagenProductoInput(required=True)

    imagen = graphene.Field(ImagenProductoType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, input, **kwargs):
        usuario = kwargs["current_user"]

        try:
            img = ImagenProducto.objects.get(
                pk=input.imagen_id,
                fecha_eliminacion__isnull=True
            )
        except ImagenProducto.DoesNotExist:
            raise GraphQLError("Imagen no encontrada")

        if img.producto.tienda.propietario != usuario and not (usuario.es_admin or usuario.es_moderador):
            raise GraphQLError("No autorizado")

        if input.nombre:
            img.nombre = input.nombre
        if input.descripcion:
            img.descripcion = input.descripcion
        if input.archivo:
            img.archivo = input.archivo

        img.save()

        return EditarImagenProducto(
            imagen=img,
            mensaje="Imagen actualizada correctamente"
        )

# Actualizar estado del producto

class ActualizarEstadoProducto(graphene.Mutation):
    class Arguments:
        tienda_producto_id = graphene.ID(required=True)
        estado_id = graphene.ID(required=True)

    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, tienda_producto_id, estado_id, **kwargs):
        usuario = kwargs["current_user"]

        try:
            tp = TiendaProducto.objects.get(pk=tienda_producto_id)
        except TiendaProducto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")

        if tp.tienda.propietario != usuario and not (usuario.es_admin or usuario.es_moderador):
            raise GraphQLError("No autorizado")

        tp.estado_id = estado_id
        tp.save()

        return ActualizarEstadoProducto(mensaje="Estado actualizado")
    
# Mutacion para actualizar stock y precio
class ActualizarStockPrecio(graphene.Mutation):
    class Arguments:
        tienda_producto_id = graphene.ID(required=True)
        precio = graphene.Float()
        stock = graphene.Int()

    producto_tienda = graphene.Field(TiendaProductoType)
    mensaje = graphene.String()

    @requiere_autenticacion(user_types=['usuario'])
    def mutate(self, info, tienda_producto_id, precio=None, stock=None, **kwargs):
        usuario = kwargs["current_user"]

        try:
            tp = TiendaProducto.objects.get(pk=tienda_producto_id)
        except TiendaProducto.DoesNotExist:
            raise GraphQLError("Producto no encontrado")

        if tp.tienda.propietario != usuario and not (usuario.es_admin or usuario.es_moderador):
            raise GraphQLError("No autorizado")

        if precio is not None:
            tp.precio = precio
        if stock is not None:
            tp.stock = stock

        tp.save()

        return ActualizarStockPrecio(
            producto_tienda=tp,
            mensaje="Stock/Precio actualizados"
        )

# ============= MUTACIONES DE TALLAS =============
# (Solo moderadores pueden gestionar tallas globales)

class CrearTallaInput(graphene.InputObjectType):
    nombre = graphene.String(required=True)

class EditarTallaInput(graphene.InputObjectType):
    nombre = graphene.String()


class CrearTalla(graphene.Mutation):
    """Crea una nueva talla. Solo moderadores y superadmins."""
    class Arguments:
        input = CrearTallaInput(required=True)
    
    talla = graphene.Field(TallaType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def mutate(self, info, input, **kwargs):
        usuario = kwargs['current_user']
        user_type = kwargs['user_type']
        
        # Verificar duplicados
        if Talla.objects.filter(
            nombre__iexact=input.nombre,
            fecha_eliminacion__isnull=True
        ).exists():
            raise GraphQLError("Ya existe una talla con ese nombre")
        
        # Crear talla
        talla = Talla(
            nombre=input.nombre.upper(),
            estado=Estado.get_activo()
        )
        talla.save()
        
        # Auditoría
        Auditoria.registrar(
            usuario=usuario,
            accion="crear_talla",
            descripcion=f"{user_type.capitalize()} {usuario.email} creó la talla '{talla.nombre}'",
            usuario_tipo=user_type
        )
        
        return CrearTalla(
            talla=talla,
            mensaje=f"Talla '{talla.nombre}' creada exitosamente"
        )


class EditarTalla(graphene.Mutation):
    """Edita una talla. Solo moderadores y superadmins."""
    class Arguments:
        id = graphene.ID(required=True)
        input = EditarTallaInput(required=True)
    
    talla = graphene.Field(TallaType)
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def mutate(self, info, id, input, **kwargs):
        usuario = kwargs['current_user']
        user_type = kwargs['user_type']
        
        try:
            talla = Talla.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Talla.DoesNotExist:
            raise GraphQLError("Talla no encontrada")
        
        nombre_anterior = talla.nombre
        
        if input.nombre:
            nombre_normalizado = input.nombre.upper()
            
            if Talla.objects.filter(
                nombre__iexact=nombre_normalizado,
                fecha_eliminacion__isnull=True
            ).exclude(pk=id).exists():
                raise GraphQLError("Ya existe otra talla con ese nombre")
            
            talla.nombre = nombre_normalizado
        
        talla.save()
        
        # Auditoría
        Auditoria.registrar(
            usuario=usuario,
            accion="editar_talla",
            descripcion=f"{user_type.capitalize()} {usuario.email} editó talla de '{nombre_anterior}' a '{talla.nombre}'",
            usuario_tipo=user_type
        )
        
        return EditarTalla(talla=talla, mensaje="Talla actualizada")


class EliminarTalla(graphene.Mutation):
    """Elimina una talla. Verifica que no haya productos usándola."""
    class Arguments:
        id = graphene.ID(required=True)
    
    ok = graphene.Boolean()
    mensaje = graphene.String()
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def mutate(self, info, id, **kwargs):
        usuario = kwargs['current_user']
        user_type = kwargs['user_type']
        
        try:
            talla = Talla.objects.get(pk=id, fecha_eliminacion__isnull=True)
        except Talla.DoesNotExist:
            raise GraphQLError("Talla no encontrada")
        
        # Verificar uso
        productos_con_talla = talla.productos_tienda.filter(
            fecha_eliminacion__isnull=True
        ).count()
        
        if productos_con_talla > 0:
            raise GraphQLError(
                f"No se puede eliminar. {productos_con_talla} producto(s) usan esta talla"
            )
        
        nombre_talla = talla.nombre
        
        # Soft delete
        talla.fecha_eliminacion = timezone.now()
        talla.estado = Estado.get_inactivo()
        talla.save()
        
        # Auditoría
        Auditoria.registrar(
            usuario=usuario,
            accion="eliminar_talla",
            descripcion=f"{user_type.capitalize()} {usuario.email} eliminó talla '{nombre_talla}'",
            usuario_tipo=user_type
        )
        
        return EliminarTalla(ok=True, mensaje=f"Talla '{nombre_talla}' eliminada")


class CrearTallasMasivas(graphene.Mutation):
    """Crea múltiples tallas. Útil para inicializar el sistema."""
    class Arguments:
        nombres = graphene.List(graphene.String, required=True)
    
    tallas = graphene.List(TallaType)
    cantidad_creadas = graphene.Int()
    mensaje = graphene.String()
    errores = graphene.List(graphene.String)
    
    @requiere_autenticacion(user_types=['moderador', 'superadmin'])
    def mutate(self, info, nombres, **kwargs):
        usuario = kwargs['current_user']
        user_type = kwargs['user_type']
        
        tallas_creadas = []
        errores = []
        
        for nombre in nombres:
            nombre_normalizado = nombre.upper().strip()
            
            if Talla.objects.filter(
                nombre__iexact=nombre_normalizado,
                fecha_eliminacion__isnull=True
            ).exists():
                errores.append(f"'{nombre_normalizado}' ya existe")
                continue
            
            try:
                talla = Talla.objects.create(
                    nombre=nombre_normalizado,
                    estado=Estado.get_activo()
                )
                tallas_creadas.append(talla)
            except Exception as e:
                errores.append(f"Error en '{nombre_normalizado}': {str(e)}")
        
        cantidad = len(tallas_creadas)
        
        if cantidad > 0:
            nombres_creados = ", ".join([t.nombre for t in tallas_creadas])
            Auditoria.registrar(
                usuario=usuario,
                accion="crear_tallas_masivas",
                descripcion=f"{user_type.capitalize()} {usuario.email} creó {cantidad} tallas: {nombres_creados}",
                usuario_tipo=user_type
            )
        
        mensaje = f"Se crearon {cantidad} tallas"
        if errores:
            mensaje += f". {len(errores)} omitidas"
        
        return CrearTallasMasivas(
            tallas=tallas_creadas,
            cantidad_creadas=cantidad,
            mensaje=mensaje,
            errores=errores if errores else None
        )

class ProductosMutaciones(graphene.ObjectType):
    # Productos
    crear_producto = CrearProducto.Field()
    editar_producto = EditarProducto.Field()
    eliminar_producto = EliminarProducto.Field()
    subir_imagen_producto = SubirImagenProducto.Field()
    eliminar_imagen_producto = EliminarImagenProducto.Field()
    editar_imagen_producto = EditarImagenProducto.Field()
    actualizar_estado_producto = ActualizarEstadoProducto.Field()
    actualizar_stock_precio = ActualizarStockPrecio.Field()
    
    # Tallas
    crear_talla = CrearTalla.Field()
    editar_talla = EditarTalla.Field()
    eliminar_talla = EliminarTalla.Field()
    crear_tallas_masivas = CrearTallasMasivas.Field()
