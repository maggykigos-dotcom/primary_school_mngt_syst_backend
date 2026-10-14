from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Grade


@receiver(post_migrate)
def create_default_grades(sender, **kwargs):
    # Create default grades only when that name does not exist.
    # If duplicate names already exist, leave them untouched.
    grades = [f"Grade {i}" for i in range(1, 7)]

    for grade in grades:
        if not Grade.objects.filter(name=grade).exists():
            Grade.objects.create(name=grade)




# from django.db.models.signals import post_migrate
# from django.dispatch import receiver
# from .models import Grade


# @receiver(post_migrate)
# def create_default_grades(sender, **kwargs):
#     grades = [f"Grade {i}" for i in range(1, 7)]

#     for grade in grades:
#         Grade.objects.get_or_create(name=grade)