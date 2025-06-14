from django.contrib.auth.backends import BaseBackend
from gestion_escolar.models import Usuario
from django.contrib.auth.hashers import check_password

class UsuarioAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            usuario = Usuario.objects.get(username=username)
            if usuario.activo and check_password(password, usuario.password_hash):
                return usuario
        except Usuario.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None
