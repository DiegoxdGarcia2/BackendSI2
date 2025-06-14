# gestion_escolar/serializers.py
from rest_framework import serializers
from .models import (
    Alumno, Profesor, Curso, Materia, AsignacionCursoMateria, Inscripcion,
    Nota, Asistencia, ActividadProyecto, EntregaActividad, Participacion,
    Tutor, AlumnoTutor, Usuario
)

class AlumnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumno
        fields = '__all__' # Incluye todos los campos del modelo

class ProfesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profesor
        fields = '__all__'

class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = '__all__'

class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = '__all__'

class AsignacionCursoMateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionCursoMateria
        fields = '__all__'

class InscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscripcion
        fields = '__all__'

class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = '__all__'

class AsistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistencia
        fields = '__all__'

class ActividadProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadProyecto
        fields = '__all__'

class EntregaActividadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntregaActividad
        fields = '__all__'

class ParticipacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participacion
        fields = '__all__'

class TutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutor
        fields = '__all__'

class AlumnoTutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlumnoTutor
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        # Excluye password_hash en la lectura, pero inclúyelo para la escritura
        fields = [
            'id', 'username', 'email', 'rol', 'activo',
            'fecha_creacion', 'ultima_sesion', 'alumno', 'profesor', 'tutor', 'password_hash'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'ultima_sesion']
        extra_kwargs = {'password_hash': {'write_only': True}} # Solo escritura para seguridad

    def create(self, validated_data):
        # Cifra la contraseña antes de guardarla
        password = validated_data.pop('password_hash', None)
        user = Usuario(**validated_data)
        if password is not None:
            from django.contrib.auth.hashers import make_password
            user.password_hash = make_password(password) # Usar make_password de Django
        user.save()
        return user

    def update(self, instance, validated_data):
        # Permite actualizar la contraseña si se proporciona
        password = validated_data.pop('password_hash', None)
        if password is not None:
            from django.contrib.auth.hashers import make_password
            instance.password_hash = make_password(password)
        return super().update(instance, validated_data)