from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Student, Teacher, Parent


@receiver(post_save, sender=User)
def create_profiles(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'student':
            Student.objects.create(user=instance)
        elif instance.role == 'teacher':
            Teacher.objects.create(user=instance)
        elif instance.role == 'parent':
            Parent.objects.create(user=instance)