from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Grade


@receiver(post_migrate)
def create_default_grades(sender, **kwargs):
    grades = [f"Grade {i}" for i in range(1, 7)]
    
    for grade in grades:
        Grade.objects.get_or_create(name=grade)