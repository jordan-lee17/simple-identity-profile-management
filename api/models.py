from django.db import models

# Create your models here.
class Person(models.Model):
    legal_name = models.CharField(max_length=255)
    preferred_name = models.CharField(max_length=255)
    professional_title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.legal_name
