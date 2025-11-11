from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Add additional fields here as needed.
    """
    # Example additional fields:
    # bio = models.TextField(max_length=500, blank=True)
    # birth_date = models.DateField(null=True, blank=True)
    # phone_number = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username
