from django.db import models
# from accounts.models import Student, Teacher

class Grade(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# 🏫 CLASS (e.g Grade 1 → Class A, B)
class SchoolClass(models.Model):
    teacher = models.ForeignKey('accounts.Teacher',on_delete=models.CASCADE)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=10)  # A, B, C

    def __str__(self):
        return f"{self.grade} - {self.name}"


# 🏫 SECTION (optional grouping)
class Section(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.school_class} - {self.name}"


# 📘 SUBJECT
# class Subject(models.Model):
#     name = models.CharField(max_length=100)
#     school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='subjects')

class Subject(models.Model):
    name = models.CharField(max_length=100)

    # assign to specific grades
    grades = models.ManyToManyField(
        'academics.Grade',
        blank=True,
        related_name='subjects'
    )

    # optional: assign to specific classes (if needed)
    school_classes = models.ManyToManyField(
        'academics.SchoolClass',
        blank=True,
        related_name='subjects'
    )
    teachers = models.ManyToManyField(
        'accounts.Teacher',
        blank=True,
        related_name='subjects'
    )

    # global subject (for all grades)
    is_for_all = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# 📅 ATTENDANCE

class Attendance(models.Model):

    STATUS_CHOICES = (
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused"),
    )

    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="attendance"
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="present"
    )

    reason = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-date", "student__user__last_name"]

        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"],
                name="unique_student_attendance_per_day"
            )
        ]

        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["school_class", "date"]),
            models.Index(fields=["student", "date"]),
        ]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"



# # 📝 EXAM RESULTS

class ExamResult(models.Model):
    TERM_CHOICES = (
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'),
        ('Term 3', 'Term 3'),
    )

    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='results'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='exam_results'
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='exam_results'
    )

    term = models.CharField(
        max_length=10,
        choices=TERM_CHOICES
    )

    session = models.CharField(
        max_length=10
    )

    marks = models.IntegerField()

    grade = models.CharField(
        max_length=5
    )

    class Meta:
        unique_together = (
            'student',
            'subject',
            'school_class',
            'term',
            'session'
        )

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.term}"



# 📝 ASSIGNMENTS
class Assignment(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    teacher = models.ForeignKey(
        "accounts.Teacher",
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    title = models.CharField(max_length=200)

    description = models.TextField(
        blank=True,
        default=""
    )

    attachment = models.FileField(
        upload_to="assignments/",
        blank=True,
        null=True
    )

    due_date = models.DateField(
        null=True,
        blank=True
    )

    max_marks = models.PositiveIntegerField(
        default=100
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.title} - {self.school_class}"
class QuizQuestion(models.Model):
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question = models.TextField()

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
        ]
    )

    marks = models.PositiveIntegerField(default=1)

    order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.assignment.title} - Question {self.order}"

# 🗓️ TIMETABLE
class Timetable(models.Model):
    DAY_CHOICES = (
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
    )

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('accounts.Teacher', on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, null=True, blank=True)
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

# ==========================================================
# TERM PERFORMANCE REPORT
# ==========================================================

class TermPerformanceReport(models.Model):
    student = models.ForeignKey(
        "accounts.Student",
        on_delete=models.CASCADE,
        related_name="term_performance_reports"
    )

    term = models.CharField(
        max_length=10,
        choices=ExamResult.TERM_CHOICES
    )

    session = models.CharField(
        max_length=10
    )

    # Official report uploaded by parent/admin
    report_file = models.FileField(
        upload_to="term_reports/",
        blank=True,
        null=True
    )

    uploaded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_term_performance_reports"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "term", "session"],
                name="unique_student_term_performance_report"
            )
        ]
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.student} - {self.term} - {self.session}"    
