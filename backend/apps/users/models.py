from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UsuarioManager(BaseUserManager):

    def create_user(self, usuario, email, nome, sobrenome, password=None, **extra_fields):
        if not email:
            raise ValueError('O usuário deve possuir um email.')

        email = self.normalize_email(email)

        user = self.model(
            usuario=usuario,
            email=email,
            nome=nome,
            sobrenome=sobrenome,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, usuario, email, nome, sobrenome, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(
            usuario=usuario,
            email=email,
            nome=nome,
            sobrenome=sobrenome,
            password=password,
            **extra_fields
        )


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    sobrenome = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    usuario = models.CharField(max_length=100, unique=True)

    foto_perfil = models.CharField(
        max_length=500,
        null=True,
        blank=True
    )

    cargo = models.CharField(max_length=100)
    e_socio = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    
    modalidades = models.ManyToManyField(
        'modalidades.ModalidadeEsportiva',
        related_name='usuarios',
        blank=True
    ) # O django cria uma tabela intermediária automaticamente para o relacionamento n para n, então não precisamos criar uma tabela separada para isso.
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'usuario'
    REQUIRED_FIELDS = ['nome', 'sobrenome', 'email']

    def __str__(self):
        return self.usuario