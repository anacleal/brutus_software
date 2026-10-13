from django.conf import settings
from django.db import models
 
 
class PasswordResetToken(models.Model):
    """Guarda apenas o hash do token"""
 
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reset_tokens",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        db_table = "password_reset_tokens"
        indexes = [models.Index(fields=["usuario", "expires_at"])]
 