import os, jwt
from datetime import timedelta
import datetime

import django
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db import models
import uuid
from uuid import UUID
from json import JSONEncoder


class UserManager(BaseUserManager):
    def create_user(self, password, first_name, email=None):

        user = self.model(first_name=first_name, email=self.normalize_email(email))
        user.set_password(password)
        user.is_active = True
        user.save()
        return user


class UserAccount(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(primary_key=True, editable=True, default=uuid.uuid4, blank=False, unique=True,
                               max_length=500, name=("user_id"), verbose_name=("User ID"))
    first_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=False, null=False)
    is_email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    signup_date = models.DateField(auto_now_add=True)
    jwt_secret = models.UUIDField(default=uuid.uuid4)
    last_login = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return "{}".format(self.user_id)

    def __user_id__(self):
        return self.user_id

    class Meta:
        db_table = 'user_account'
        managed = True

    @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        dt = datetime.datetime.now() + timedelta(days=60)

        token = jwt.encode({
            'id': self.pk,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')

