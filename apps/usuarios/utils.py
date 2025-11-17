import jwt
from datetime import datetime, timedelta
from django.conf import settings
from .models import Usuario, Moderador, SuperAdministrador

JWT_SECRET = getattr(settings, 'SECRET_KEY')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_HOURS = getattr(settings, 'JWT_EXPIRATION_HOURS', 24)



def crear_token(user_id, user_type):
    # Crea un token JWT para el usuario identificando el tipo de usuario
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXP_DELTA_HOURS),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decodificar_token(token):
    # Decodifica y valida el token JWT y verifica si es valido
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Si el token esta expirado
    except jwt.InvalidTokenError:
        return None  # Si el token es inválido

def obtener_usuario_desde_contexto(info):
    request = info.context
    auth_header = request.headers.get('Authorization', '')

    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
    elif auth_header.startswith('JWT '):
        token = auth_header.replace('JWT ', '')
    else:
        return None, None

    payload = decodificar_token(token)
    if not payload:
        return None, None

    user_id = payload.get('user_id')
    user_type = payload.get('user_type')

    try:
        if user_type == 'usuario':
            usuario = Usuario.objects.get(id=user_id)
        elif user_type == 'moderador':
            usuario = Moderador.objects.get(id=user_id)
        elif user_type == 'superadmin':
            usuario = SuperAdministrador.objects.get(id=user_id)
        else:
            return None, None

        return usuario, user_type

    except (Usuario.DoesNotExist, Moderador.DoesNotExist, SuperAdministrador.DoesNotExist):
        return None, None


def requiere_autenticacion(user_types=None):
    # Funcion decoradora para proteger resolvers en GraphQL
    def decorator(func):
        def wrapper(self, info, *args, **kwargs):
            usuario, user_type = obtener_usuario_desde_contexto(info)
            
            if not usuario:
                raise Exception("No autenticado. Token inválido o expirado.")
            
            if user_types and user_type not in user_types:
                raise Exception(f"Acceso denegado. Se requiere: {', '.join(user_types)}")
            
            # Inyecta el usuario en kwargs para usarlo en la función
            kwargs['current_user'] = usuario
            kwargs['user_type'] = user_type
            
            return func(self, info, *args, **kwargs)
        return wrapper
    return decorator