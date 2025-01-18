from django.db import models
from django.utils import timezone

class ShortenedURL(models.Model):
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=10, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    password = models.CharField(max_length=128, blank=True, null=True)
    access_count = models.IntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"

class URLAccess(models.Model):
    url = models.ForeignKey(ShortenedURL, on_delete=models.CASCADE, related_name='accesses')
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"{self.url.short_code} accessed from {self.ip_address} at {self.accessed_at}"

    class Meta:
        verbose_name_plural = "URL accesses"
