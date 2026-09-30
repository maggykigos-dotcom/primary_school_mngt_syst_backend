from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    GradeViewSet,
    SchoolClassViewSet,
    SectionViewSet,
    SubjectViewSet,
    AttendanceViewSet,
    ExamResultViewSet,
    TimetableViewSet,
    AssignmentViewSet,
    QuizQuestionViewSet,
    TermPerformanceReportViewSet
)
    
router = DefaultRouter()

router.register(r'subjects', SubjectViewSet, basename='subjects')
router.register(r'grades', GradeViewSet, basename='grades')
router.register(r'classes', SchoolClassViewSet, basename='classes')
router.register(r'sections', SectionViewSet, basename='sections')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'results', ExamResultViewSet, basename='results')
router.register(r'timetable', TimetableViewSet, basename='timetable')
router.register(r'assignments', AssignmentViewSet, basename='assignments')
router.register(
    r"quiz-questions",
    QuizQuestionViewSet,
    basename="quiz-questions"
)
router.register(
    r"term-performance-reports",
    TermPerformanceReportViewSet,
    basename="term-performance-reports"
)
urlpatterns = [
    path('', include(router.urls)),
] 

