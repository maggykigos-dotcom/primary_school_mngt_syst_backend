from django.contrib import admin
from .models import (
    Subject, Attendance,
    ExamResult, Assignment, Timetable, Grade, SchoolClass,Section,QuizQuestion
)

admin.site.register(Subject)
admin.site.register(Attendance)
admin.site.register(ExamResult)
admin.site.register(Assignment)
admin.site.register(Timetable)
admin.site.register(Grade)
admin.site.register(SchoolClass)
admin.site.register(Section)
@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "assignment",
        "order",
        "question",
        "correct_answer",
        "marks",
    )

    list_filter = (
        "assignment",
        "correct_answer",
    )

    search_fields = (
        "question",
        "assignment__title",
    )

    ordering = (
        "assignment",
        "order",
    )
