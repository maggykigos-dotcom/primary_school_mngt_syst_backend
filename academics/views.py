from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework import  serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser

from django.db import transaction
from accounts.models import Student

from .models import (
    Grade,
    SchoolClass,
    Section,
    Subject,
    Attendance,
    ExamResult,
    Assignment,
    QuizQuestion,
    Timetable,
    TermPerformanceReport,
    TeachingAssignment,
)

from .serializers import (
    GradeSerializer,
    SchoolClassSerializer,
    SectionSerializer,
    SubjectSerializer,
    AttendanceSerializer,
    ExamResultSerializer,
    AssignmentSerializer,
    BulkAttendanceSerializer,
    TimetableSerializer,
    QuizQuestionSerializer,
    StudentQuizQuestionSerializer,
    TermPerformanceReportSerializer

)

class SubjectViewSet(ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ✅ Admin
        if user.role == 'admin':
            return Subject.objects.all()

        # ✅ Student
        if user.role == 'student':
            student = getattr(user, 'student_profile', None)

            if not student or not student.school_class:
                return Subject.objects.filter(is_for_all=True)

            return Subject.objects.filter(
                Q(is_for_all=True) |
                Q(grades=student.school_class.grade) |
                Q(school_classes=student.school_class)
            ).distinct()

        # 🔥 Teacher (NOW RESTRICTED)
        if user.role == 'teacher':
            teacher = getattr(user, 'teacher_profile', None)

            if not teacher:
                return Subject.objects.none()

            return Subject.objects.filter(
                Q(teachers=teacher)
                | Q(teaching_assignments__teacher=teacher)
            ).distinct()
        return Subject.objects.none()

class GradeViewSet(ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]


class SchoolClassViewSet(ModelViewSet):
    serializer_class = SchoolClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ADMIN
        if user.role == "admin":
            return SchoolClass.objects.all()

        # TEACHER
        if user.role == "teacher":
            teacher = getattr(
                user,
                "teacher_profile",
                None
            )

            if not teacher:
                return SchoolClass.objects.none()

            return SchoolClass.objects.filter(
                Q(teacher=teacher)
                | Q(teaching_assignments__teacher=teacher)
            ).distinct()


        # STUDENT
        if user.role == "student":
            student = getattr(
                user,
                "student_profile",
                None
            )

            if not student or not student.school_class:
                return SchoolClass.objects.none()

            return SchoolClass.objects.filter(
                id=student.school_class.id
            )

        # PARENT
        if user.role == "parent":
            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:
                return SchoolClass.objects.none()

            return SchoolClass.objects.filter(
                id__in=parent.students.values_list(
                    "school_class",
                    flat=True
                )
            ).distinct()

        return SchoolClass.objects.none()


class AttendanceViewSet(ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    # ======================================================
    # QUERYSET / ROLE-BASED ACCESS
    # ======================================================

    def get_queryset(self):
        user = self.request.user

        attendance = Attendance.objects.select_related(
            "student__user",
            "school_class",
            "school_class__teacher",
        )

        # ==================================================
        # ADMIN
        # Admin can see ALL attendance records
        # ==================================================

        if user.role == "admin":
            return attendance.all()

        # ==================================================
        # TEACHER
        # Teacher can see attendance ONLY for their class
        # ==================================================

        if user.role == "teacher":
            teacher = getattr(
                user,
                "teacher_profile",
                None
            )

            if not teacher:
                return Attendance.objects.none()

            return attendance.filter(
                Q(school_class__teacher=teacher)
                | Q(school_class__teaching_assignments__teacher=teacher)
            ).distinct()


        # ==================================================
        # STUDENT
        # Student can see ONLY their own attendance
        # ==================================================

        if user.role == "student":
            student = getattr(
                user,
                "student_profile",
                None
            )

            if not student:
                return Attendance.objects.none()

            return attendance.filter(
                student=student
            )

        # ==================================================
        # PARENT
        # Parent can see ONLY their children's attendance
        # ==================================================

        if user.role == "parent":
            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:
                return Attendance.objects.none()

            return attendance.filter(
                student__in=parent.students.all()
            )

        # ==================================================
        # UNKNOWN ROLE
        # ==================================================

        return Attendance.objects.none()

    # ======================================================
    # CLASSES AVAILABLE FOR ATTENDANCE
    #
    # ADMIN:
    #   Can see ALL classes
    #
    # TEACHER:
    #   Can see ONLY classes assigned to them
    #
    # STUDENT/PARENT:
    #   Cannot access this endpoint
    #
    # IMPORTANT:
    # This endpoint also returns the students inside each
    # class so the AttendanceForm can display them.
    # ======================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="classes"
    )
    def classes(self, request):
        user = request.user

        # ==================================================
        # ADMIN
        # ==================================================

        if user.role == "admin":
            classes = SchoolClass.objects.all()

        # ==================================================
        # TEACHER
        # ==================================================

        elif user.role == "teacher":
            teacher = getattr(
                user,
                "teacher_profile",
                None
            )

            if not teacher:
                return Response(
                    {
                        "detail": "Teacher profile not found."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            classes = SchoolClass.objects.filter(
                Q(teacher=teacher)
                | Q(teaching_assignments__teacher=teacher)
            ).distinct()


        # ==================================================
        # OTHER USERS
        # ==================================================

        else:
            return Response(
                {
                    "detail": (
                        "Only admins and teachers can "
                        "access attendance classes."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ==================================================
        # LOAD STUDENTS
        # ==================================================

        classes = classes.prefetch_related(
            "students__user"
        )

        result = []

        for school_class in classes:

            students = []

            for student in school_class.students.all():

                full_name = student.user.get_full_name()

                students.append({
                    "id": student.id,
                    "name": (
                        full_name
                        or student.user.username
                    ),
                    "admission_number": (
                        student.admission_number
                    ),
                    "profile_picture": (
                        request.build_absolute_uri(
                            student.user.profile_picture.url
                        )
                        if student.user.profile_picture
                        else None
                    ),
                })

            result.append({
                "id": school_class.id,
                "name": str(school_class),
                "student_count": len(students),
                "students": students,
            })

        return Response(result)



    @action(
        detail=False,
        methods=["get"],
        url_path="my-classes"
    )
    def my_classes(self, request):
        user = request.user

        # Only teachers
        if user.role != "teacher":
            return Response(
                {
                    "detail": (
                        "Only teachers can access "
                        "their classes."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        teacher = getattr(
            user,
            "teacher_profile",
            None
        )

        if not teacher:
            return Response(
                {
                    "detail": "Teacher profile not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        classes = (
            SchoolClass.objects
            .filter(
                Q(teacher=teacher)
                | Q(teaching_assignments__teacher=teacher)
            )
            .distinct()
            .prefetch_related("students__user")
        )
        result = []

        for school_class in classes:

            students = []

            for student in school_class.students.all():

                full_name = student.user.get_full_name()

                students.append({
                    "id": student.id,
                    "name": (
                        full_name
                        or student.user.username
                    ),
                    "admission_number": (
                        student.admission_number
                    ),
                    "profile_picture": (
                        request.build_absolute_uri(
                           student.user.profile_picture.url
                        )
                        if student.user.profile_picture
                        else None
                    ),
                })

            result.append({
                "id": school_class.id,
                "name": str(school_class),
                "student_count": len(students),
                "students": students,
            })

        return Response(result)

    @action(
        detail=False,
        methods=["post"],
        url_path="bulk"
    )
    def bulk_attendance(self, request):

        # ==================================================
        # ONLY ADMIN AND TEACHERS
        # ==================================================

        if request.user.role not in [
            "teacher",
            "admin"
        ]:
            return Response(
                {
                    "detail": (
                        "You do not have permission "
                        "to record attendance."
                    )
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ==================================================
        # VALIDATE REQUEST
        # ==================================================

        serializer = BulkAttendanceSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        school_class_id = (
            serializer.validated_data["school_class"]
        )

        date = serializer.validated_data["date"]

        attendance_data = (
            serializer.validated_data["attendance"]
        )

        # ==================================================
        # GET CLASS
        # ==================================================

        try:
            school_class = SchoolClass.objects.get(
                id=school_class_id
            )

        except SchoolClass.DoesNotExist:
            return Response(
                {
                    "school_class": (
                        "School class not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # ==================================================
        # TEACHER SECURITY
        #
        # Teachers can ONLY record attendance for
        # their own class.
        #
        # Admins can record for ANY class.
        # ==================================================

        if request.user.role == "teacher":

            teacher = getattr(
                request.user,
                "teacher_profile",
                None
            )

            if not teacher:
                return Response(
                    {
                        "detail": (
                            "Teacher profile not found."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            if not (
                school_class.teacher_id == teacher.id
                or TeachingAssignment.objects.filter(
                    teacher=teacher,
                    school_class=school_class,
                ).exists()
            ):
               return Response(
                    {
                        "detail": (
                            "You can only record attendance for "
                            "your own class or a class assigned to you."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        # ==================================================
        # GET STUDENTS
        # ==================================================

        student_ids = [
            item["student"]
            for item in attendance_data
        ]

        students = {
            student.id: student
            for student in (
                school_class.students.filter(
                    id__in=student_ids
                )
            )
        }

        # ==================================================
        # MAKE SURE EVERY STUDENT BELONGS TO THE CLASS
        # ==================================================

        missing_students = [
            student_id
            for student_id in student_ids
            if student_id not in students
        ]

        if missing_students:
            return Response(
                {
                    "attendance": (
                        "One or more students do not "
                        "belong to this class."
                    ),
                    "students": missing_students,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ==================================================
        # SAVE ATOMICALLY
        # ==================================================

        saved_records = []

        with transaction.atomic():

            for item in attendance_data:

                student = students[
                    item["student"]
                ]

                attendance, created = (
                    Attendance.objects.update_or_create(
                        student=student,
                        date=date,
                        defaults={
                            "school_class": school_class,
                            "status": item["status"],
                            "reason": (
                                item.get("reason")
                                or ""
                            ),
                        }
                    )
                )

                saved_records.append(
                    attendance
                )

        # ==================================================
        # RESPONSE
        # ==================================================

        return Response(
            {
                "message": (
                    "Attendance saved successfully."
                ),
                "date": date,
                "school_class": school_class.id,
                "records_saved": len(
                    saved_records
                ),
            },
            status=status.HTTP_200_OK
        )




class SectionViewSet(ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ADMIN
        if user.role == "admin":
            return Section.objects.all()

        # TEACHER
        if user.role == "teacher":
            teacher = getattr(
                user,
                "teacher_profile",
                None
            )

            if not teacher:
                return Section.objects.none()

            return Section.objects.filter(
                Q(school_class__teacher=teacher)
                | Q(school_class__teaching_assignments__teacher=teacher)
            ).distinct()


        # STUDENT
        if user.role == "student":
            student = getattr(
                user,
                "student_profile",
                None
            )

            if not student or not student.school_class:
                return Section.objects.none()

            return Section.objects.filter(
                school_class=student.school_class
            )

        # PARENT
        if user.role == "parent":
            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:
                return Section.objects.none()

            class_ids = parent.students.values_list(
                "school_class",
                flat=True
            )

            return Section.objects.filter(
                school_class__in=class_ids
            ).distinct()

        return Section.objects.none()


# class ExamResultViewSet(ModelViewSet):
class ExamResultViewSet(ModelViewSet):
    """
    Role-based Exam Result ViewSet.

    ADMIN
        - View all results
        - Create results
        - Update results
        - Delete results

    TEACHER
        - View results for subjects they teach
        - Create results for subjects they teach
        - Update results for subjects they teach
        - Delete results for subjects they teach

    PARENT
        - View results belonging to their children
        - Cannot create/update/delete results

    STUDENT
        - View their own results
        - Cannot create/update/delete results
    """

    serializer_class = ExamResultSerializer
    permission_classes = [IsAuthenticated]

    # ==========================================================
    # QUERYSET
    # ==========================================================

    def get_queryset(self):
        user = self.request.user

        queryset = ExamResult.objects.select_related(
            "student",
            "student__user",
            "subject",
            "school_class",
            "school_class__grade",
        )

        # ======================================================
        # ADMIN
        # ======================================================

        if user.role == "admin":
            return queryset.all()


        # ======================================================
        # STUDENT
        # ======================================================

        if user.role == "student":

            student = getattr(
                user,
                "student_profile",
                None
            )

            if not student:
                return queryset.none()

            return queryset.filter(student=student)

        # ======================================================
        # PARENT
        # ======================================================

        if user.role == "parent":

            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:
                return queryset.none()
                # return ExamResult.objects.none()

            return queryset.filter(
                student__in=parent.students.all()
            )

            # return ExamResult.objects.select_related(
            #     "student",
            #     "student__user",
            #     "subject",
            #     "school_class",
            #     "school_class__grade",
            # ).filter(
            #     student__in=parent.students.all()
            # )

        # ======================================================
        # TEACHER
        # ======================================================

        if user.role == "teacher":

            teacher = getattr(
                user,
                "teacher_profile",
                None
            )

            if not teacher:
                return queryset.none()
                # return ExamResult.objects.none()

            assignments = TeachingAssignment.objects.filter(
                teacher=teacher
            ).values_list(
                "school_class_id",
                "subject_id"
            )

            allowed_combinations = Q(pk__in=[])

            for class_id, subject_id in assignments:
                allowed_combinations |= Q(
                    school_class_id=class_id,
                    subject_id=subject_id
                )

            return queryset.filter(
                allowed_combinations
            ).distinct()

        return queryset.none()
            # return ExamResult.objects.select_related(
            #     "student",
            #     "student__user",
            #     "subject",
            #     "school_class",
            #     "school_class__grade",
            # ).filter(
            #     subject__in=teacher.subjects.all()
            # )

        # ======================================================
        # UNKNOWN ROLE
        # ======================================================

        return ExamResult.objects.none()

    # ==========================================================
    # CREATE
    # ==========================================================
    def perform_create(self, serializer):
        user = self.request.user

        # Only admins and teachers can create results
        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to enter exam results."
            )

        student = serializer.validated_data.get("student")
        subject = serializer.validated_data.get("subject")

        # Make sure a student was selected
        if not student:
            raise serializers.ValidationError({
                "student": "Please select a valid student."
            })

        # Get the class automatically from the selected student
        school_class = student.school_class

        # Make sure the student has a class assigned
        if not school_class:
            raise serializers.ValidationError({
                "student": "This student has no school class assigned. "
                        "Please assign the student to a class first."
            })

        # Teachers must have the exact subject-and-class assignment
        if user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher:
                raise PermissionDenied(
                    "Teacher profile not found."
                )

            assigned = TeachingAssignment.objects.filter(
                teacher=teacher,
                subject=subject,
                school_class=school_class,
            ).exists()

            if not assigned:
                raise PermissionDenied(
                    "You can only enter results for subjects and classes "
                    "assigned to you."
                )

        # Save the result with the student's actual class
        serializer.save(school_class=school_class)

        # user = self.request.user

        # # ------------------------------------------------------
        # # Only Admin and Teacher can create results
        # # ------------------------------------------------------

        # if user.role not in ["admin", "teacher"]:
        #     from rest_framework.exceptions import PermissionDenied

        #     raise PermissionDenied(
        #         "You do not have permission to enter exam results."
        #     )

        # # ------------------------------------------------------
        # # Teacher can only enter results for subjects they teach
        # # ------------------------------------------------------

        # if user.role == "teacher":

        #     teacher = getattr(
        #         user,
        #         "teacher_profile",
        #         None
        #     )

        #     if not teacher:
        #         from rest_framework.exceptions import PermissionDenied

        #         raise PermissionDenied(
        #             "Teacher profile not found."
        #         )

        #     subject = serializer.validated_data.get(
        #         "subject"
        #     )

        #     if not teacher.subjects.filter(
        #         id=subject.id
        #     ).exists():

        #         from rest_framework.exceptions import PermissionDenied

        #         raise PermissionDenied(
        #             "You can only enter results for subjects "
        #             "you teach."
        #         )

        # serializer.save()

    # ==========================================================
    # UPDATE
    # ==========================================================

    def perform_update(self, serializer):

        user = self.request.user

        # Only admins and teachers can update results
        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to edit exam results."
            )

        instance = serializer.instance

        # Use submitted values, or retain existing values
        student = serializer.validated_data.get(
            "student",
            instance.student
        )
        subject = serializer.validated_data.get(
            "subject",
            instance.subject
        )
        school_class = serializer.validated_data.get(
            "school_class",
            instance.school_class
        )

        # Ensure the student belongs to the selected class
        if student.school_class_id != school_class.id:
            raise serializers.ValidationError({
                "student": "This student does not belong to the selected class."
            })

        # Teachers must be assigned to the exact subject and class
        if user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher:
                raise PermissionDenied(
                    "Teacher profile not found."
                )

            assigned = TeachingAssignment.objects.filter(
                teacher=teacher,
                subject=subject,
                school_class=school_class,
            ).exists()

            if not assigned:
                raise PermissionDenied(
                    "You can only edit results for subjects and classes assigned to you."
                )

        serializer.save()
        # user = self.request.user

        # # ------------------------------------------------------
        # # Only Admin and Teacher can update
        # # ------------------------------------------------------

        # if user.role not in ["admin", "teacher"]:
        #     from rest_framework.exceptions import PermissionDenied

        #     raise PermissionDenied(
        #         "You do not have permission to edit exam results."
        #     )

        # # ------------------------------------------------------
        # # Teacher subject restriction
        # # ------------------------------------------------------

        # if user.role == "teacher":

        #     teacher = getattr(
        #         user,
        #         "teacher_profile",
        #         None
        #     )

        #     if not teacher:
        #         from rest_framework.exceptions import PermissionDenied

        #         raise PermissionDenied(
        #             "Teacher profile not found."
        #         )

        #     subject = serializer.validated_data.get(
        #         "subject",
        #         serializer.instance.subject
        #     )

        #     if not teacher.subjects.filter(
        #         id=subject.id
        #     ).exists():

        #         from rest_framework.exceptions import PermissionDenied

        #         raise PermissionDenied(
        #             "You can only edit results for subjects "
        #             "you teach."
        #         )

        # serializer.save()

    # ==========================================================
    # DELETE
    # ==========================================================
    def perform_destroy(self, instance):
        user = self.request.user

        # Only admins and teachers can delete results
        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to delete exam results."
            )

        # Teachers can delete results only for their assignments
        if user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher:
                raise PermissionDenied(
                    "Teacher profile not found."
                )

            assigned = TeachingAssignment.objects.filter(
                teacher=teacher,
                subject=instance.subject,
                school_class=instance.school_class,
            ).exists()

            if not assigned:
                raise PermissionDenied(
                    "You can only delete results for subjects and classes assigned to you."
                )

        instance.delete()
    #     user = self.request.user

    #     # ------------------------------------------------------
    #     # Only Admin and Teacher can delete
    #     # ------------------------------------------------------

    #     if user.role not in ["admin", "teacher"]:
    #         from rest_framework.exceptions import PermissionDenied

    #         raise PermissionDenied(
    #             "You do not have permission to delete exam results."
    #         )

    #     # ------------------------------------------------------
    #     # Teacher subject restriction
    #     # ------------------------------------------------------

    #     if user.role == "teacher":

    #         teacher = getattr(
    #             user,
    #             "teacher_profile",
    #             None
    #         )

    #         if not teacher:
    #             from rest_framework.exceptions import PermissionDenied

    #             raise PermissionDenied(
    #                 "Teacher profile not found."
    #             )

    #         if not teacher.subjects.filter(
    #             id=instance.subject.id
    #         ).exists():

    #             from rest_framework.exceptions import PermissionDenied

    #             raise PermissionDenied(
    #                 "You can only delete results for subjects "
    #                 "you teach."
    #             )

    #     instance.delete()



        # ==========================================================
        # TERM PERFORMANCE SUMMARY
        # ==========================================================
    @action(
        detail=False,
        methods=["get"],
        url_path="term-performance"
    )
    def term_performance(self, request):
        """
        Return term performance for a student.

        Results are calculated from the subjects that have already
        been recorded. A student does NOT need results for every
        subject before performance can be displayed.
        """

        student_id = request.query_params.get("student")
        term = request.query_params.get("term")
        session = request.query_params.get("session")

        # ---------------------------------------------------------
        # VALIDATE REQUIRED PARAMETERS
        # ---------------------------------------------------------

        if not student_id:
            return Response(
                {"detail": "Student is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not term:
            return Response(
                {"detail": "Term is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not session:
            return Response(
                {"detail": "Session is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------------------------
        # GET STUDENT
        # ---------------------------------------------------------

        try:
            student = Student.objects.select_related(
                "user",
                "school_class__grade"
            ).get(pk=student_id)

        except Student.DoesNotExist:
            return Response(
                {"detail": "Student not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # ---------------------------------------------------------
        # ROLE-BASED ACCESS
        # ---------------------------------------------------------

        user = request.user

        if user.role == "parent":
            if not student in user.parent_profile.students.all():
                return Response(
                    {"detail": "You do not have permission to view this student's performance."},
                    status=status.HTTP_403_FORBIDDEN
                )

        elif user.role == "student":
            if not hasattr(user, "student_profile") or user.student_profile.id != student.id:
                return Response(
                    {"detail": "You do not have permission to view this student's performance."},
                    status=status.HTTP_403_FORBIDDEN
                )

        elif user.role == "teacher":
            # Teachers can only view students in their own classes.
            teacher_profile = getattr(user, "teacher_profile", None)

            if not teacher_profile:
                return Response(
                    {"detail": "Teacher profile not found."},
                    status=status.HTTP_403_FORBIDDEN
                )

            if not student.school_class:
                return Response(
                    {"detail": "This student is not assigned to a class."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if student.school_class.teacher_id != teacher_profile.id:
                return Response(
                    {"detail": "You do not have permission to view this student's performance."},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Admin can view everything.

        # ---------------------------------------------------------
        # CHECK STUDENT CLASS
        # ---------------------------------------------------------

        school_class = student.school_class

        if not school_class:
            return Response(
                {
                    "detail": "This student is not assigned to a school class.",
                    "has_performance": False,
                },
                status=status.HTTP_200_OK
            )

        # ---------------------------------------------------------
        # FIND SUBJECTS FOR THE STUDENT'S CLASS
        # ---------------------------------------------------------

        subjects = Subject.objects.filter(
            Q(is_for_all=True)
            | Q(grades=school_class.grade)
            | Q(school_classes=school_class)
        ).distinct()

        total_subjects = subjects.count()

        # ---------------------------------------------------------
        # GET RESULTS THAT HAVE ACTUALLY BEEN POSTED
        # ---------------------------------------------------------

        results = ExamResult.objects.filter(
            student=student,
            school_class=school_class,
            term=term,
            session=session,
            subject__in=subjects
        ).select_related(
            "subject"
        ).order_by(
            "subject__name"
        )

        posted_subjects = results.count()

        # ---------------------------------------------------------
        # CALCULATE AVERAGE FROM POSTED RESULTS
        # ---------------------------------------------------------

        if posted_subjects > 0:
            total_marks = sum(
                float(result.marks)
                for result in results
            )

            average = round(
                total_marks / posted_subjects,
                2
            )
        else:
            average = None

        # ---------------------------------------------------------
        # CALCULATE OVERALL GRADE
        # ---------------------------------------------------------

        if average is None:
            overall_grade = None

        elif average >= 80:
            overall_grade = "A"

        elif average >= 70:
            overall_grade = "B"

        elif average >= 60:
            overall_grade = "C"

        elif average >= 50:
            overall_grade = "D"

        else:
            overall_grade = "E"

        # ---------------------------------------------------------
        # PREPARE SUBJECT RESULTS
        # ---------------------------------------------------------

        result_data = []

        for result in results:
            result_data.append({
                "id": result.id,
                "subject": result.subject.name,
                "marks": float(result.marks),
                "grade": result.grade,
                "term": result.term,
                "session": result.session,
            })

        # ---------------------------------------------------------
        # SUBJECT PROGRESS
        # ---------------------------------------------------------

        remaining_subjects = max(
            total_subjects - posted_subjects,
            0
        )

        all_results_posted = (
            total_subjects > 0
            and posted_subjects >= total_subjects
        )

        # ---------------------------------------------------------
        # RETURN RESPONSE
        # ---------------------------------------------------------

        return Response(
            {
                "student": student.id,
                "student_name": student.user.get_full_name(),
                "class": school_class.name,
                "grade": school_class.grade.name if school_class.grade else None,
                "term": term,
                "session": session,

                "total_subjects": total_subjects,
                "posted_subjects": posted_subjects,
                "remaining_subjects": remaining_subjects,

                "average": average,
                "overall_grade": overall_grade,

                "all_results_posted": all_results_posted,
                "has_performance": posted_subjects > 0,

                "results": result_data,
            },
            status=status.HTTP_200_OK
        )


# ==========================================================
# TERM PERFORMANCE REPORT
# ==========================================================

class TermPerformanceReportViewSet(ModelViewSet):

    serializer_class = TermPerformanceReportSerializer

    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    # ------------------------------------------------------
    # QUERYSET
    # ------------------------------------------------------

    def get_queryset(self):

        user = self.request.user

        queryset = TermPerformanceReport.objects.select_related(
            "student",
            "student__user",
            "student__school_class",
            "student__school_class__grade",
            "uploaded_by",
        )

        # ADMIN
        if user.role == "admin":
            return queryset.all()

        # PARENT
        if user.role == "parent":

            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:
                return queryset.none()

            return queryset.filter(
                student__in=parent.students.all()
            )

        # STUDENT
        if user.role == "student":

            student = getattr(
                user,
                "student_profile",
                None
            )

            if not student:
                return queryset.none()

            return queryset.filter(
                student=student
            )

        # TEACHER
        # Teachers don't need access to uploaded parent reports.
        return queryset.none()

    # ------------------------------------------------------
    # CREATE / UPLOAD
    # ------------------------------------------------------

    def perform_create(self, serializer):

        user = self.request.user

        # Only parent and admin can upload
        if user.role not in ["parent", "admin"]:

            raise PermissionDenied(
                "Only parents and admins can upload "
                "term performance reports."
            )

        student = serializer.validated_data.get(
            "student"
        )

        if not student:

            raise PermissionDenied(
                "Student is required."
            )

        # --------------------------------------------------
        # PARENT SECURITY
        # --------------------------------------------------

        if user.role == "parent":

            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:

                raise PermissionDenied(
                    "Parent profile not found."
                )

            if not parent.students.filter(
                id=student.id
            ).exists():

                raise PermissionDenied(
                    "You can only upload reports "
                    "for your own children."
                )

        # --------------------------------------------------
        # SAVE
        # --------------------------------------------------

        serializer.save(
            uploaded_by=user
        )

    # ------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------

    def perform_update(self, serializer):

        user = self.request.user

        if user.role != "admin":

            raise PermissionDenied(
                "Only administrators can replace "
                "term performance reports."
            )

        serializer.save()

    # ------------------------------------------------------
    # DELETE
    # ------------------------------------------------------

    def perform_destroy(self, instance):

        user = self.request.user

        if user.role != "admin":

            raise PermissionDenied(
                "Only administrators can delete "
                "term performance reports."
            )

        instance.delete()

class AssignmentViewSet(ModelViewSet):

    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ADMIN
        if user.role == "admin":
            return Assignment.objects.all()

        # TEACHER
        if user.role == "teacher":
            teacher = getattr(
                user,
                "teacher_profile",
                None
            )

            if not teacher:
                return Assignment.objects.none()

            return Assignment.objects.filter(
                teacher=teacher
            )

        # STUDENT
        if user.role == "student":
            student = getattr(
                user,
                "student_profile",
                None
            )

            if not student or not student.school_class:
                return Assignment.objects.none()

            return Assignment.objects.filter(
                school_class=student.school_class
            )

        # PARENT
        if user.role == "parent":
            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:
                return Assignment.objects.none()

            class_ids = parent.students.values_list(
                "school_class",
                flat=True
            )

            return Assignment.objects.filter(
                school_class__in=class_ids
            ).distinct()

        return Assignment.objects.none()
    def perform_create(self, serializer):
        user = self.request.user

        # Only admins and teachers can create assignments
        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to create assignments."
            )

        if user.role == "admin":
            serializer.save()
            return

        teacher = getattr(user, "teacher_profile", None)

        if not teacher:
            raise PermissionDenied("Teacher profile not found.")

        assigned_teacher = serializer.validated_data.get("teacher")
        subject = serializer.validated_data.get("subject")
        school_class = serializer.validated_data.get("school_class")

        if assigned_teacher != teacher:
            raise PermissionDenied(
                "You can only create assignments under your own teacher profile."
            )

        if not TeachingAssignment.objects.filter(
            teacher=teacher,
            subject=subject,
            school_class=school_class,
        ).exists():
            raise PermissionDenied(
                "You are not assigned to teach this subject in this class."
            )

        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user

        # Only admins and teachers can update assignments
        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to edit assignments."
            )

        if user.role == "admin":
            serializer.save()
            return

        teacher = getattr(user, "teacher_profile", None)

        if not teacher:
            raise PermissionDenied("Teacher profile not found.")

        instance = serializer.instance

        assigned_teacher = serializer.validated_data.get(
            "teacher", instance.teacher
        )
        subject = serializer.validated_data.get(
            "subject", instance.subject
        )
        school_class = serializer.validated_data.get(
            "school_class", instance.school_class
        )

        if instance.teacher != teacher or assigned_teacher != teacher:
            raise PermissionDenied(
                "You can only edit your own assignments."
            )

        if not TeachingAssignment.objects.filter(
            teacher=teacher,
            subject=subject,
            school_class=school_class,
        ).exists():
            raise PermissionDenied(
                "You are not assigned to teach this subject in this class."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        # Only admins and teachers can delete assignments
        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to delete assignments."
            )

        if user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher or instance.teacher != teacher:
                raise PermissionDenied(
                    "You can only delete your own assignments."
                )

        instance.delete()
class QuizQuestionViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            queryset = QuizQuestion.objects.select_related(
                "assignment",
                "assignment__school_class",
                "assignment__subject",
            ).all()

        elif user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher:
                return QuizQuestion.objects.none()

            queryset = QuizQuestion.objects.filter(
                assignment__teacher=teacher
            ).select_related(
                "assignment",
                "assignment__school_class",
                "assignment__subject",
            )

        elif user.role == "student":
            student = getattr(user, "student_profile", None)

            if not student or not student.school_class:
                return QuizQuestion.objects.none()

            queryset = QuizQuestion.objects.filter(
                assignment__school_class=student.school_class
            ).select_related(
                "assignment",
                "assignment__school_class",
                "assignment__subject",
            )

        else:
            return QuizQuestion.objects.none()

        # Allow:
        # /api/academics/quiz-questions/?assignment=5
        assignment_id = self.request.query_params.get("assignment")

        if assignment_id:
            queryset = queryset.filter(
                assignment_id=assignment_id
            )

        return queryset

    def get_serializer_class(self):
        if self.request.user.role == "student":
            return StudentQuizQuestionSerializer

        return QuizQuestionSerializer

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == "admin":
            serializer.save()
            return

        if user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher:
                raise PermissionDenied(
                    "Teacher profile not found."
                )

            assignment = serializer.validated_data.get("assignment")

            if not assignment:
                raise PermissionDenied(
                    "Assignment is required."
                )

            if assignment.teacher != teacher:
                raise PermissionDenied(
                    "You can only add questions to your own assignments."
                )

            serializer.save()
            return

        raise PermissionDenied(
            "You do not have permission to create quiz questions."
        )

    def perform_update(self, serializer):
        user = self.request.user

        if user.role == "admin":
            serializer.save()
            return

        if user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher:
                raise PermissionDenied(
                    "Teacher profile not found."
                )

            current_assignment = self.get_object().assignment

            new_assignment = serializer.validated_data.get(
                "assignment",
                current_assignment
            )

            if current_assignment.teacher != teacher:
                raise PermissionDenied(
                    "You can only edit questions from your own assignments."
                )

            if new_assignment.teacher != teacher:
                raise PermissionDenied(
                    "You cannot move this question to another teacher's assignment."
                )

            serializer.save()
            return

        raise PermissionDenied(
            "You do not have permission to edit quiz questions."
        )

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role == "admin":
            instance.delete()
            return

        if user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher:
                raise PermissionDenied(
                    "Teacher profile not found."
                )

            if instance.assignment.teacher != teacher:
                raise PermissionDenied(
                    "You can only delete questions from your own assignments."
                )

            instance.delete()
            return

        raise PermissionDenied(
            "You do not have permission to delete quiz questions."
        )

class TimetableViewSet(ModelViewSet):
    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ADMIN
        if user.role == "admin":
            queryset = Timetable.objects.all()

        # TEACHER
        elif user.role == "teacher":
            teacher = getattr(
                user,
                "teacher_profile",
                None
            )

            if not teacher:
                return Timetable.objects.none()

            queryset = Timetable.objects.filter(
                teacher=teacher
            )

        # STUDENT
        elif user.role == "student":
            student = getattr(
                user,
                "student_profile",
                None
            )

            if not student or not student.school_class:
                return Timetable.objects.none()

            queryset = Timetable.objects.filter(
                school_class=student.school_class
            )

        # PARENT
        elif user.role == "parent":
            parent = getattr(
                user,
                "parent_profile",
                None
            )

            if not parent:
                return Timetable.objects.none()

            class_ids = parent.students.values_list(
                "school_class",
                flat=True
            )

            queryset = Timetable.objects.filter(
                school_class__in=class_ids
            ).distinct()

        else:
            return Timetable.objects.none()

        # FILTER BY DAY
        day = self.request.query_params.get("day")

        if day:
            queryset = queryset.filter(day=day)

        # ORDER BY DAY AND TIME
        return queryset.order_by(
            "day",
            "start_time"
        )


    def perform_create(self, serializer):
        user = self.request.user

        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to create timetables."
            )

        # Admins can manage all timetables
        if user.role == "admin":
            serializer.save()
            return

        teacher = getattr(user, "teacher_profile", None)

        if not teacher:
            raise PermissionDenied("Teacher profile not found.")

        assigned_teacher = serializer.validated_data.get("teacher")
        subject = serializer.validated_data.get("subject")
        school_class = serializer.validated_data.get("school_class")

        if assigned_teacher != teacher:
            raise PermissionDenied(
                "You can only create timetables under your own teacher profile."
            )

        # When a class is selected, require an exact teaching assignment
        if school_class:
            assigned = TeachingAssignment.objects.filter(
                teacher=teacher,
                subject=subject,
                school_class=school_class,
            ).exists()

            if not assigned:
                raise PermissionDenied(
                    "You are not assigned to teach this subject in this class."
                )

        # Preserve support for timetables without a selected class
        elif not subject.teachers.filter(id=teacher.id).exists():
            raise PermissionDenied(
                "You are not assigned to teach this subject."
            )

        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user

        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to edit timetables."
            )

        if user.role == "admin":
            serializer.save()
            return

        teacher = getattr(user, "teacher_profile", None)

        if not teacher:
            raise PermissionDenied("Teacher profile not found.")

        instance = serializer.instance

        assigned_teacher = serializer.validated_data.get(
            "teacher", instance.teacher
        )
        subject = serializer.validated_data.get(
            "subject", instance.subject
        )
        school_class = serializer.validated_data.get(
            "school_class", instance.school_class
        )

        if instance.teacher != teacher or assigned_teacher != teacher:
            raise PermissionDenied(
                "You can only edit your own timetables."
            )

        if school_class:
            assigned = TeachingAssignment.objects.filter(
                teacher=teacher,
                subject=subject,
                school_class=school_class,
            ).exists()

            if not assigned:
                raise PermissionDenied(
                    "You are not assigned to teach this subject in this class."
                )

        elif not subject.teachers.filter(id=teacher.id).exists():
            raise PermissionDenied(
                "You are not assigned to teach this subject."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role not in ["admin", "teacher"]:
            raise PermissionDenied(
                "You do not have permission to delete timetables."
            )

        if user.role == "teacher":
            teacher = getattr(user, "teacher_profile", None)

            if not teacher or instance.teacher != teacher:
                raise PermissionDenied(
                    "You can only delete your own timetables."
                )

        instance.delete()
