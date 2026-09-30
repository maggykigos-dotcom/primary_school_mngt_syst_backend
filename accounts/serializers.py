from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import update_last_login

from .models import User, Student, Parent, Teacher
from django.db import transaction

# ==========================================================
# USER SERIALIZER
# ==========================================================

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


# ==========================================================
# TEACHER SERIALIZER
# ==========================================================

class TeacherSerializer(serializers.ModelSerializer):

    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    date_of_birth = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Teacher

        fields = [
            "id",
            "name",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "date_of_birth",
            "address",
            "role",
            "is_active",
            "is_staff",
            "profile_picture",
        ]

    def get_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return ""

    def get_username(self, obj):
        if obj.user:
            return obj.user.username
        return ""

    def get_first_name(self, obj):
        if obj.user:
            return obj.user.first_name or ""
        return ""

    def get_last_name(self, obj):
        if obj.user:
            return obj.user.last_name or ""
        return ""

    def get_phone_number(self, obj):
        if obj.user:
            return obj.user.phone_number or ""
        return ""

    def get_email(self, obj):
        if obj.user:
            return obj.user.email or ""
        return ""

    def get_date_of_birth(self, obj):
        if obj.user and obj.user.date_of_birth:
            return obj.user.date_of_birth
        return None

    def get_address(self, obj):
        if obj.user:
            return obj.user.address or ""
        return ""

    def get_role(self, obj):
        if obj.user:
            return obj.user.role or ""
        return ""

    def get_is_active(self, obj):
        if obj.user:
            return obj.user.is_active
        return False

    def get_is_staff(self, obj):
        if obj.user:
            return obj.user.is_staff
        return False

    def get_profile_picture(self, obj):
        if obj.user and obj.user.profile_picture:
            request = self.context.get("request")

            if request:
                return request.build_absolute_uri(
                    obj.user.profile_picture.url
                )

            return obj.user.profile_picture.url

        return None


# class TeacherSerializer(serializers.ModelSerializer):
#     username = serializers.SerializerMethodField()
#     phone_number = serializers.SerializerMethodField()
#     email = serializers.SerializerMethodField()
#     name = serializers.SerializerMethodField()
#     profile_picture = serializers.SerializerMethodField()

#     class Meta:
#         model = Teacher
#         fields = [
#             "id",
#             "name",
#             "username",
#             "phone_number",
#             "email",
#             "profile_picture",
#         ]

#     def get_name(self, obj):
#         if obj.user:
#             return obj.user.get_full_name() or obj.user.username
#         return ""

#     def get_username(self, obj):
#         if obj.user:
#             return obj.user.username
#         return ""

#     def get_phone_number(self, obj):
#         if obj.user:
#             return obj.user.phone_number or ""
#         return ""

#     def get_email(self, obj):
#         if obj.user:
#             return obj.user.email or ""
#         return ""

#     def get_profile_picture(self, obj):
#         if obj.user and obj.user.profile_picture:
#             request = self.context.get("request")

#             if request:
#                 return request.build_absolute_uri(
#                     obj.user.profile_picture.url
#                 )

#             return obj.user.profile_picture.url

#         return None





# ==========================================================
# STUDENT SERIALIZER
# ==========================================================

class StudentSerializer(serializers.ModelSerializer):

    # ==========================================================
    # USER INFORMATION
    # ==========================================================

    username = serializers.CharField(
        write_only=True
    )

    password = serializers.CharField(
        write_only=True
    )

    first_name = serializers.CharField(
        write_only=True
    )

    last_name = serializers.CharField(
        write_only=True
    )

    email = serializers.EmailField(
        write_only=True,
        required=False,
        allow_blank=True
    )

    phone_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )

    date_of_birth = serializers.DateField(
        write_only=True,
        required=False,
        allow_null=True
    )

    address = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )

    # ==========================================================
    # READ-ONLY USER INFORMATION
    # ==========================================================

    username_display = serializers.SerializerMethodField()
    first_name_display = serializers.SerializerMethodField()
    last_name_display = serializers.SerializerMethodField()
    email_display = serializers.SerializerMethodField()
    phone_number_display = serializers.SerializerMethodField()
    date_of_birth_display = serializers.SerializerMethodField()
    address_display = serializers.SerializerMethodField()

    # ==========================================================
    # STUDENT INFORMATION
    # ==========================================================

    student_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()

    class Meta:
        model = Student

        fields = [
            "id",

            # -----------------------------
            # Fields used when creating/editing
            # -----------------------------
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "date_of_birth",
            "address",

            # -----------------------------
            # Fields returned when viewing
            # -----------------------------
            "username_display",
            "first_name_display",
            "last_name_display",
            "email_display",
            "phone_number_display",
            "date_of_birth_display",
            "address_display",

            # -----------------------------
            # Student information
            # -----------------------------
            "student_name",
            "profile_picture",
            "school_class",
            "class_name",
            "admission_number",
        ]

        read_only_fields = [
            "id",
            "admission_number",
            "student_name",
            "profile_picture",
            "class_name",
            "username_display",
            "first_name_display",
            "last_name_display",
            "email_display",
            "phone_number_display",
            "date_of_birth_display",
            "address_display",
        ]

    # ==========================================================
    # VALIDATE USERNAME
    # ==========================================================

    def validate_username(self, value):

        if User.objects.filter(
            username__iexact=value
        ).exists():

            raise serializers.ValidationError(
                "This username already exists. "
                "Please choose another username."
            )

        return value

    # ==========================================================
    # STUDENT NAME
    # ==========================================================

    def get_student_name(self, obj):

        if obj.user:

            return (
                obj.user.get_full_name()
                or obj.user.username
            )

        return ""

    # ==========================================================
    # USERNAME
    # ==========================================================

    def get_username_display(self, obj):

        if obj.user:
            return obj.user.username

        return ""

    # ==========================================================
    # FIRST NAME
    # ==========================================================

    def get_first_name_display(self, obj):

        if obj.user:
            return obj.user.first_name

        return ""

    # ==========================================================
    # LAST NAME
    # ==========================================================

    def get_last_name_display(self, obj):

        if obj.user:
            return obj.user.last_name

        return ""

    # ==========================================================
    # EMAIL
    # ==========================================================

    def get_email_display(self, obj):

        if obj.user:
            return obj.user.email

        return ""

    # ==========================================================
    # PHONE NUMBER
    # ==========================================================

    def get_phone_number_display(self, obj):

        if obj.user:
            return obj.user.phone_number

        return ""

    # ==========================================================
    # DATE OF BIRTH
    # ==========================================================

    def get_date_of_birth_display(self, obj):

        if obj.user and obj.user.date_of_birth:
            return obj.user.date_of_birth

        return None

    # ==========================================================
    # ADDRESS
    # ==========================================================

    def get_address_display(self, obj):

        if obj.user:
            return obj.user.address

        return ""

    # ==========================================================
    # PROFILE PICTURE
    # ==========================================================

    def get_profile_picture(self, obj):

        if obj.user and obj.user.profile_picture:

            request = self.context.get("request")

            if request:

                return request.build_absolute_uri(
                    obj.user.profile_picture.url
                )

            return obj.user.profile_picture.url

        return None

    # ==========================================================
    # CLASS NAME
    # ==========================================================

    def get_class_name(self, obj):

        if not obj.school_class:
            return ""

        grade = obj.school_class.grade

        grade_name = (
            grade.name
            if grade
            else ""
        )

        class_name = (
            obj.school_class.name
            or ""
        )

        if grade_name and class_name:

            return f"{grade_name} - {class_name}"

        return class_name or grade_name

    # ==========================================================
    # CREATE STUDENT
    # ==========================================================

    @transaction.atomic
    def create(self, validated_data):

        # -----------------------------
        # USER FIELDS
        # -----------------------------

        username = validated_data.pop(
            "username"
        )

        password = validated_data.pop(
            "password"
        )

        first_name = validated_data.pop(
            "first_name"
        )

        last_name = validated_data.pop(
            "last_name"
        )

        email = validated_data.pop(
            "email",
            ""
        )

        phone_number = validated_data.pop(
            "phone_number",
            ""
        )

        date_of_birth = validated_data.pop(
            "date_of_birth",
            None
        )

        address = validated_data.pop(
            "address",
            ""
        )

        # -----------------------------
        # STUDENT FIELDS
        # -----------------------------

        school_class = validated_data.pop(
            "school_class",
            None
        )

        # -----------------------------
        # CREATE USER
        # -----------------------------

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role="student",
            phone_number=phone_number,
            date_of_birth=date_of_birth,
            address=address,
        )

        # -----------------------------
        # GET STUDENT CREATED BY SIGNAL
        # -----------------------------

        student = Student.objects.get(
            user=user
        )

        # -----------------------------
        # ASSIGN SCHOOL CLASS
        # -----------------------------

        if school_class is not None:

            student.school_class = school_class
            student.save()

        return student


# class StudentSerializer(serializers.ModelSerializer):
#     username = serializers.CharField(write_only=True)
#     password = serializers.CharField(write_only=True)

#     first_name = serializers.CharField(write_only=True)
#     last_name = serializers.CharField(write_only=True)

#     email = serializers.EmailField(
#         write_only=True,
#         required=False,
#         allow_blank=True
#     )

#     phone_number = serializers.CharField(
#         write_only=True,
#         required=False,
#         allow_blank=True
#     )

#     date_of_birth = serializers.DateField(
#         write_only=True,
#         required=False,
#         allow_null=True
#     )

#     address = serializers.CharField(
#         write_only=True,
#         required=False,
#         allow_blank=True
#     )

#     student_name = serializers.SerializerMethodField()
#     profile_picture = serializers.SerializerMethodField()
#     class_name = serializers.SerializerMethodField()

#     class Meta:
#         model = Student

#         fields = [
#             "id",

#             # User information
#             "username",
#             "password",
#             "first_name",
#             "last_name",
#             "email",
#             "phone_number",
#             "date_of_birth",
#             "address",

#             # Student information
#             "student_name",
#             "profile_picture",
#             "school_class",
#             "class_name",
#             "admission_number",
#         ]

#         read_only_fields = [
#             "id",
#             "admission_number",
#             "student_name",
#             "profile_picture",
#             "class_name",
#         ]

#     # ==========================================================
#     # VALIDATE USERNAME
#     # ==========================================================

#     def validate_username(self, value):
#         if User.objects.filter(username__iexact=value).exists():
#             raise serializers.ValidationError(
#                 "This username already exists. Please choose another username."
#             )

#         return value

#     # ==========================================================
#     # STUDENT NAME
#     # ==========================================================

#     def get_student_name(self, obj):
#         if obj.user:
#             return (
#                 obj.user.get_full_name()
#                 or obj.user.username
#             )

#         return ""

#     # ==========================================================
#     # PROFILE PICTURE
#     # ==========================================================

#     def get_profile_picture(self, obj):
#         if obj.user and obj.user.profile_picture:
#             request = self.context.get("request")

#             if request:
#                 return request.build_absolute_uri(
#                     obj.user.profile_picture.url
#                 )

#             return obj.user.profile_picture.url

#         return None

#     # ==========================================================
#     # CLASS NAME
#     # ==========================================================

  
#     def get_class_name(self, obj):

#         if not obj.school_class:
#             return ""

#         grade = obj.school_class.grade
#         grade_name = grade.name if grade else ""

#         class_name = obj.school_class.name or ""

#         if grade_name and class_name:
#             return f"{grade_name} - {class_name}"
            

#         return class_name or grade_name    
       

#     # ==========================================================
#     # CREATE STUDENT
#     # ==========================================================

#     @transaction.atomic
#     def create(self, validated_data):

#         # -----------------------------
#         # USER FIELDS
#         # -----------------------------

#         username = validated_data.pop("username")
#         password = validated_data.pop("password")

#         first_name = validated_data.pop("first_name")
#         last_name = validated_data.pop("last_name")

#         email = validated_data.pop("email", "")
#         phone_number = validated_data.pop("phone_number", "")

#         date_of_birth = validated_data.pop(
#             "date_of_birth",
#             None
#         )

#         address = validated_data.pop(
#             "address",
#             ""
#         )

#         # -----------------------------
#         # STUDENT FIELDS
#         # -----------------------------

#         school_class = validated_data.pop(
#             "school_class",
#             None
#         )

#         # -----------------------------
#         # CREATE USER
#         # -----------------------------

#         user = User.objects.create_user(
#             username=username,
#             password=password,
#             first_name=first_name,
#             last_name=last_name,
#             email=email,
#             role="student",
#             phone_number=phone_number,
#             date_of_birth=date_of_birth,
#             address=address,
#         )

#         # -----------------------------
#         # GET STUDENT CREATED BY SIGNAL
#         # -----------------------------

#         student = Student.objects.get(
#             user=user
#         )

#         # -----------------------------
#         # ASSIGN SCHOOL CLASS
#         # -----------------------------

#         if school_class is not None:
#             student.school_class = school_class
#             student.save()

#         return student




# ==========================================================
# PARENT SERIALIZER
# ==========================================================
class ParentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Parent
        fields = [
            "id",
            "user",
            "name",
            "username",
            "phone_number",
            "profile_picture",
            "role_type",
            "students",
        ]

    def get_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return ""

    def get_username(self, obj):
        if obj.user:
            return obj.user.username
        return ""

    def get_phone_number(self, obj):
        if obj.user:
            return obj.user.phone_number or ""
        return ""

    def get_profile_picture(self, obj):
        if obj.user and obj.user.profile_picture:
            request = self.context.get("request")

            if request:
                return request.build_absolute_uri(
                    obj.user.profile_picture.url
                )

            return obj.user.profile_picture.url
            
            return None



class CustomTokenSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):

        data = super().validate(attrs)

        # Update last login
        update_last_login(None, self.user)

        # Profile picture URL
        profile_picture = None

        if self.user.profile_picture:
            request = self.context.get("request")

            if request:
                profile_picture = request.build_absolute_uri(
                    self.user.profile_picture.url
                )
            else:
                profile_picture = self.user.profile_picture.url

        # Custom user information
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "role": self.user.role,
            "profile_picture": profile_picture,
        }

        return data



