import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
# from academics.models import SchoolClass


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('student', 'Student'),
        ('bursar', 'Bursar'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    def __str__(self):
        return self.get_full_name() or self.username


class Student(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='student_profile',limit_choices_to={'role': 'student'})
    admission_number = models.CharField(max_length=50, unique=True, editable=False)
    school_class = models.ForeignKey('academics.SchoolClass',on_delete=models.SET_NULL,null=True,blank=True,related_name='students')

    def save(self, *args, **kwargs):
        if not self.admission_number:
            self.admission_number = self.generate_admission_number()
        super().save(*args, **kwargs)

    def generate_admission_number(self):
        return f"ADM-{uuid.uuid4().hex[:6].upper()}"

    def __str__(self):
        return f"{self.user} ({self.admission_number})"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    # Teacher can have many students
    students = models.ManyToManyField('accounts.Student',related_name='teachers',blank=True
)


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    # Parent has children
    students = models.ManyToManyField('accounts.Student', related_name='parents', blank=True)
    role_type = models.CharField(
        choices=[
            ('mother', 'Mother'),
            ('father', 'Father'),
            ('guardian', 'Guardian')
        ],
        
        max_length=10
    )
