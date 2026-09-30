from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import User, Student, Teacher, Parent
from .serializers import (
    StudentSerializer,
    ParentSerializer,
    UserSerializer,
    TeacherSerializer,
    CustomTokenSerializer,
)
from .permissions import IsAdmin
from rest_framework_simplejwt.views import TokenObtainPairView


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsAdmin]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':
            return User.objects.all()

        if user.role == 'teacher':
            students = user.teacher_profile.students.all()
            return User.objects.filter(
                student_profile__in=students
            )

        if user.role == 'parent':
            students = user.parent_profile.students.all()
            return User.objects.filter(
                student_profile__in=students
            )

        if user.role == 'student':
            return User.objects.filter(id=user.id)

        return User.objects.none()

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ==========================
        # ADMIN
        # ==========================
        if user.role == "admin":
            return Student.objects.all()

        # ==========================
        # TEACHER
        # ==========================
        if user.role == "teacher":
            teacher = getattr(
                user,
                "teacher_profile",
                None
            )

            if not teacher:
                return Student.objects.none()

            # Students belonging to classes taught by this teacher
            return Student.objects.filter(
                school_class__teacher=teacher
            ).select_related(
                "user",
                "school_class",
                "school_class__grade"
            )

        # ==========================
        # STUDENT
        # ==========================
        if user.role == "student":
            student = getattr(
                user,
                "student_profile",
                None
            )

            if not student:
                return Student.objects.none()

            return Student.objects.filter(
                id=student.id
            )

        # ==========================
        # PARENT
        # ==========================
        if user.role == "parent":
            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:
                return Student.objects.none()

            return parent.students.all().select_related(
                "user",
                "school_class",
                "school_class__grade"
            )

        return Student.objects.none()

    @action(
        detail=False,
        methods=["get"],
        url_path="profile"
    )
    def profile(self, request):
        if request.user.role != "student":
            return Response(
                {
                    "detail": "Only students can access their profile."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {
                    "detail": "Student profile not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(student)
        return Response(serializer.data)


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ==========================
        # ADMIN
        # ==========================
        if user.role == "admin":
            return Teacher.objects.all()

        # ==========================
        # TEACHER
        # ==========================
        if user.role == "teacher":
            return Teacher.objects.filter(
                user=user
            ).select_related("user")

        return Teacher.objects.none()

    @action(
        detail=False,
        methods=["get"],
        url_path="profile"
    )
    def profile(self, request):

        # Only teachers can access their profile
        if request.user.role != "teacher":
            return Response(
                {
                    "detail": "Only teachers can access their profile."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            return Response(
                {
                    "detail": "Teacher profile not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(teacher)

        return Response(serializer.data)




class ParentViewSet(viewsets.ModelViewSet):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':
            return Parent.objects.all()

        if user.role == 'parent':
            return Parent.objects.filter(user=user)

        return Parent.objects.none()

    @action(
        detail=False,
        methods=['get'],
        url_path='children'
    )
    def children(self, request):

        if request.user.role != 'parent':
            return Response(
                {
                    'detail': 'Only parents can access their children.'
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            parent = request.user.parent_profile
        except Parent.DoesNotExist:
            return Response(
                {
                    'detail': 'Parent profile not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        children = parent.students.all()

        serializer = StudentSerializer(
            children,
            many=True
        )

        return Response(serializer.data)


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer








