from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Student, Teacher, Parent


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + (
        (
            "School Information",
            {
                "fields": (
                    "role",
                    "date_of_birth",
                    "phone_number",
                    "address",
                    "profile_picture",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "School Information",
            {
                "fields": (
                    "role",
                    "date_of_birth",
                    "phone_number",
                    "address",
                    "profile_picture",
                )
            },
        ),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "admission_number", "school_class")


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user",)


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("user",)


# from django.contrib import admin
# from .models import User, Student, Teacher, Parent

# admin.site.register(User)
# admin.site.register(Student)
# admin.site.register(Teacher)
# admin.site.register(Parent)
