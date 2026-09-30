from rest_framework import serializers
from .models import (
    Subject,
    Grade,
    SchoolClass,
    Section,
    Attendance,
    ExamResult,
    Timetable,
    Assignment,
    QuizQuestion,
    TermPerformanceReport,
)

from accounts.models import Teacher, Student


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['id', 'name']


# class SchoolClassSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SchoolClass
#         fields = ['id', 'name', 'grade', 'teacher']

class SchoolClassSerializer(serializers.ModelSerializer):

    grade_name = serializers.CharField(
        source='grade.name',
        read_only=True
    )

    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = SchoolClass
        fields = [
            'id',
            'name',
            'grade',
            'grade_name',
            'teacher',
            'teacher_name',
        ]

    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return obj.teacher.user.get_full_name()

        return None

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'name', 'school_class']



class SubjectSerializer(serializers.ModelSerializer):
    grades = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Grade.objects.all(),
        required=False
    )

    school_classes = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SchoolClass.objects.all(),
        required=False
    )

    teachers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Teacher.objects.all(),
        required=False
    )

    class Meta:
        model = Subject

        fields = [
            "id",
            "name",
            "grades",
            "school_classes",
            "teachers",
            "is_for_all",
        ]

    def validate(self, data):
        is_for_all = data.get(
            "is_for_all",
            getattr(
                self.instance,
                "is_for_all",
                False
            )
        )

        grades = data.get("grades")
        school_classes = data.get("school_classes")

        if is_for_all and (
            grades or school_classes
        ):
            raise serializers.ValidationError(
                "Cannot assign grades or classes when "
                "subject is for all."
            )

        return data


# -----------------------------
# ATTENDANCE
# -----------------------------

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.user.get_full_name",
        read_only=True
    )

    profile_picture = serializers.SerializerMethodField()

    school_class_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendance

        fields = [
            "id",
            "student",
            "student_name",
            "profile_picture",
            "school_class",
            "school_class_name",
            "date",
            "status",
            "reason",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "school_class",
            "school_class_name",
            "profile_picture",
            "created_at",
            "updated_at",
        ]

    def get_profile_picture(self, obj):
        request = self.context.get("request")

        try:
            profile_picture = (
                obj.student.user.profile_picture
            )

            if (
                profile_picture
                and profile_picture.name
            ):
                if request:
                    return request.build_absolute_uri(
                        profile_picture.url
                    )

                return profile_picture.url

        except Exception:
            pass

        return None

    def get_school_class_name(self, obj):
        if obj.school_class:
            return str(obj.school_class)

        return None

    def validate(self, data):
        student = data.get("student")

        if not student:
            raise serializers.ValidationError({
                "student": "Student is required."
            })

        if not student.school_class:
            raise serializers.ValidationError({
                "student": (
                    "This student has not been assigned "
                    "to a class."
                )
            })

        return data

    def create(self, validated_data):
        student = validated_data["student"]

        validated_data["school_class"] = (
            student.school_class
        )

        return Attendance.objects.create(
            **validated_data
        )

    def update(self, instance, validated_data):
        # Never allow school_class to be manually changed
        validated_data.pop(
            "school_class",
            None
        )

        return super().update(
            instance,
            validated_data
        )
# # # -----------------------------
# # # ATTENDANCE
# # # -----------------------------

# class AttendanceSerializer(serializers.ModelSerializer):
#     student_name = serializers.CharField(
#         source="student.user.get_full_name",
#         read_only=True
#     )

#     school_class_name = serializers.SerializerMethodField()

#     class Meta:
#         model = Attendance

#         fields = [
#             "id",
#             "student",
#             "student_name",
#             "school_class",
#             "school_class_name",
#             "date",
#             "status",
#             "reason",
#             "created_at",
#             "updated_at",
#         ]

#         read_only_fields = [
#             "school_class",
#             "school_class_name",
#             "created_at",
#             "updated_at",
#         ]

#     def get_school_class_name(self, obj):
#         if obj.school_class:
#             return str(obj.school_class)

#         return None

#     def validate(self, data):
#         student = data.get("student")

#         if not student:
#             raise serializers.ValidationError({
#                 "student": "Student is required."
#             })

#         if not student.school_class:
#             raise serializers.ValidationError({
#                 "student": (
#                     "This student has not been assigned "
#                     "to a class."
#                 )
#             })

#         return data

#     def create(self, validated_data):
#         student = validated_data["student"]

#         validated_data["school_class"] = student.school_class

#         return Attendance.objects.create(
#             **validated_data
#         )

#     def update(self, instance, validated_data):
#         # Never allow school_class to be manually changed
#         validated_data.pop("school_class", None)

#         return super().update(
#             instance,
#             validated_data
#         )

class BulkAttendanceItemSerializer(serializers.Serializer):

    student = serializers.IntegerField()

    status = serializers.ChoiceField(
        choices=[
            "present",
            "absent",
            "late",
            "excused",
        ]
    )

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )


class BulkAttendanceSerializer(serializers.Serializer):

    school_class = serializers.IntegerField()

    date = serializers.DateField()

    attendance = BulkAttendanceItemSerializer(
        many=True
    )

    def validate(self, data):

        attendance = data["attendance"]

        if not attendance:
            raise serializers.ValidationError({
                "attendance": "At least one student attendance record is required."
            })

        student_ids = [
            item["student"]
            for item in attendance
        ]

        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError({
                "attendance": "A student appears more than once."
            })

        return data

# -----------------------------
# EXAM RESULTS
# -----------------------------

class ExamResultSerializer(serializers.ModelSerializer):
    """
    Serializer for exam results.

    The student's school_class is automatically taken from
    the selected student.

    The exam grade is automatically calculated from marks.
    """

    student_name = serializers.CharField(
        source="student.user.get_full_name",
        read_only=True
    )

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    class_name = serializers.SerializerMethodField()

    grade_name = serializers.SerializerMethodField()

    # These are automatically determined by the backend.
    school_class = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    grade = serializers.CharField(
        read_only=True
    )

    class Meta:
        model = ExamResult

        fields = [
            "id",

            # Student
            "student",
            "student_name",

            # Subject
            "subject",
            "subject_name",

            # Automatically obtained from student
            "school_class",
            "class_name",
            "grade_name",

            # Result information
            "term",
            "session",
            "marks",
            "grade",
        ]

        read_only_fields = [
            "school_class",
            "class_name",
            "grade_name",
            "grade",
        ]

    # ==========================================================
    # CLASS NAME
    # ==========================================================

    def get_class_name(self, obj):
        if obj.school_class:
            return str(obj.school_class)

        return None

    # ==========================================================
    # GRADE NAME
    # ==========================================================

    def get_grade_name(self, obj):
        if (
            obj.school_class
            and obj.school_class.grade
        ):
            return obj.school_class.grade.name

        return None

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def validate_marks(self, value):
        """
        Marks must be between 0 and 100.
        """

        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Marks must be between 0 and 100."
            )

        return value

    # ==========================================================
    # VALIDATE STUDENT
    # ==========================================================

    def validate(self, attrs):
        student = attrs.get("student")
        subject = attrs.get("subject")
        term = attrs.get("term")
        session = attrs.get("session")

        # ------------------------------------------------------
        # Student must have a class
        # ------------------------------------------------------

        if student and not student.school_class:
            raise serializers.ValidationError({
                "student": (
                    "This student has not been assigned "
                    "to a school class."
                )
            })

        # ------------------------------------------------------
        # Prevent duplicate result
        # ------------------------------------------------------

        if (
            student
            and subject
            and term
            and session
            and student.school_class
        ):
            existing = ExamResult.objects.filter(
                student=student,
                subject=subject,
                school_class=student.school_class,
                term=term,
                session=session,
            )

            # When editing an existing result, don't compare it
            # with itself.
            if self.instance:
                existing = existing.exclude(
                    pk=self.instance.pk
                )

            if existing.exists():
                raise serializers.ValidationError({
                    "result": (
                        "A result already exists for this "
                        "student, subject, term and session."
                    )
                })

        return attrs

    # ==========================================================
    # CALCULATE GRADE
    # ==========================================================

    @staticmethod
    def calculate_grade(marks):
        """
        Convert marks into an exam grade.

        Current grading scale:
            80 - 100 = A
            70 - 79  = B
            60 - 69  = C
            50 - 59  = D
            0  - 49  = E
        """

        if marks >= 80:
            return "A"

        if marks >= 70:
            return "B"

        if marks >= 60:
            return "C"

        if marks >= 50:
            return "D"

        return "E"

    # ==========================================================
    # CREATE RESULT
    # ==========================================================

    def create(self, validated_data):
        student = validated_data["student"]

        # Automatically obtain the student's class.
        validated_data["school_class"] = student.school_class

        # Automatically calculate the exam grade.
        marks = validated_data["marks"]

        validated_data["grade"] = self.calculate_grade(
            marks
        )

        return ExamResult.objects.create(
            **validated_data
        )

    # ==========================================================
    # UPDATE RESULT
    # ==========================================================

    def update(self, instance, validated_data):
        """
        Recalculate grade whenever marks are changed.

        The school class always follows the student's
        current class.
        """

        student = validated_data.get(
            "student",
            instance.student
        )

        marks = validated_data.get(
            "marks",
            instance.marks
        )

        # Automatically keep school_class synchronized
        # with the student's current class.
        validated_data["school_class"] = (
            student.school_class
        )

        # Recalculate grade.
        validated_data["grade"] = self.calculate_grade(
            marks
        )

        return super().update(
            instance,
            validated_data
        )

# ==========================================================
# TERM PERFORMANCE REPORT
# ==========================================================

class TermPerformanceReportSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.user.get_full_name",
        read_only=True
    )

    class_name = serializers.SerializerMethodField()

    report_url = serializers.SerializerMethodField()

    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TermPerformanceReport

        fields = [
            "id",
            "student",
            "student_name",
            "class_name",
            "term",
            "session",
            "report_file",
            "report_url",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
        ]

        read_only_fields = [
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
            "student_name",
            "class_name",
            "report_url",
        ]

    def get_class_name(self, obj):
        if obj.student and obj.student.school_class:
            return str(obj.student.school_class)

        return None

    def get_report_url(self, obj):
        if not obj.report_file:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.report_file.url
            )

        return obj.report_file.url

    def get_uploaded_by_name(self, obj):
        if not obj.uploaded_by:
            return None

        return obj.uploaded_by.get_full_name() or obj.uploaded_by.username

    def validate(self, data):

        student = data.get("student")

        if not student:
            raise serializers.ValidationError({
                "student": "Student is required."
            })

        if not student.school_class:
            raise serializers.ValidationError({
                "student": (
                    "This student has not been assigned "
                    "to a school class."
                )
            })

        report_file = data.get("report_file")

        if report_file:

            allowed_types = [
                "application/pdf",
                "image/jpeg",
                "image/png",
            ]

            if report_file.content_type not in allowed_types:
                raise serializers.ValidationError({
                    "report_file": (
                        "Only PDF, JPG, JPEG and PNG files "
                        "are allowed."
                    )
                })

            # 5 MB maximum
            max_size = 5 * 1024 * 1024

            if report_file.size > max_size:
                raise serializers.ValidationError({
                    "report_file": (
                        "The report file must not exceed 5 MB."
                    )
                })

        return data        

# -----------------------------
# TIMETABLE
# -----------------------------

class TimetableSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    teacher_name = serializers.SerializerMethodField()

    class_name = serializers.SerializerMethodField()

    day_name = serializers.CharField(
        source="get_day_display",
        read_only=True
    )

    class Meta:
        model = Timetable

        fields = [
            "id",
            "day",
            "day_name",
            "start_time",
            "end_time",
            "subject",
            "subject_name",
            "teacher",
            "teacher_name",
            "school_class",
            "class_name",
        ]

    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return obj.teacher.user.get_full_name()

        return "Teacher not assigned"

    def get_class_name(self, obj):
        if obj.school_class:
            return str(obj.school_class)

        return "Class not assigned"

    def validate(self, data):
        teacher = data.get("teacher")
        subject = data.get("subject")
        school_class = data.get("school_class")

        # Teacher must teach the selected subject
        if teacher and subject:
            if not subject.teachers.filter(
                id=teacher.id
            ).exists():
                raise serializers.ValidationError(
                    "Teacher is not assigned to this subject."
                )

        # Teacher must be assigned to selected class
        if teacher and school_class:
            if school_class.teacher != teacher:
                raise serializers.ValidationError(
                    "Teacher is not assigned to this class."
                )

        # End time must be after start time
        if data.get("start_time") and data.get("end_time"):
            if data["start_time"] >= data["end_time"]:
                raise serializers.ValidationError(
                    "End time must be later than start time."
                )

        return data




# -----------------------------
# ASSIGNMENT
# -----------------------------

class AssignmentSerializer(serializers.ModelSerializer):

    grade_name = serializers.CharField(
        source="school_class.grade.name",
        read_only=True
    )

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    class_name = serializers.CharField(
        source="school_class.name",
        read_only=True
    )

    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Assignment

        fields = [
            "id",
            "title",
            "description",

            # IDs - useful for forms/editing
            "teacher",
            "subject",
            "school_class",

            # Readable names - useful for displaying data
            "teacher_name",
            "subject_name",
            "class_name",
            "grade_name",

            "attachment",
            "due_date",
            "max_marks",
            "created_at",
        ]

    def get_teacher_name(self, obj):
        teacher = obj.teacher

        if not teacher:
            return "—"

        user = getattr(teacher, "user", None)

        if user:
            full_name = user.get_full_name()

            if full_name:
                return full_name

            return user.username

        return str(teacher)

    def validate(self, data):

        teacher = data.get(
            "teacher",
            getattr(self.instance, "teacher", None)
        )

        subject = data.get(
            "subject",
            getattr(self.instance, "subject", None)
        )

        school_class = data.get(
            "school_class",
            getattr(self.instance, "school_class", None)
        )

        # ==========================================
        # CHECK TEACHER-SUBJECT RELATIONSHIP
        # ==========================================

        if teacher and subject:

            if not subject.teachers.filter(
                id=teacher.id
            ).exists():

                raise serializers.ValidationError(
                    "Teacher is not assigned to this subject."
                )

        # ==========================================
        # CHECK TEACHER-CLASS RELATIONSHIP
        # ==========================================

        if teacher and school_class:

            if school_class.teacher != teacher:

                raise serializers.ValidationError(
                    "Teacher is not assigned to this class."
                )

        return data
class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "assignment",
            "question",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "marks",
            "order",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        assignment = data.get(
            "assignment",
            getattr(self.instance, "assignment", None)
        )

        if not assignment:
            raise serializers.ValidationError(
                "An assignment is required."
            )

        return data
class StudentQuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "question",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "marks",
            "order",
        ]
