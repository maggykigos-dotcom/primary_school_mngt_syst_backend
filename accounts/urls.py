from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, TeacherViewSet, ParentViewSet, UserViewSet, CustomLoginView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register('users', UserViewSet)
router.register(r'students', StudentViewSet,basename='student')
router.register(r'parents', ParentViewSet,basename='parent')
router.register('teachers', TeacherViewSet,basename='teacher')


urlpatterns = [
    path('login/', CustomLoginView.as_view()),
    path('refresh/', TokenRefreshView.as_view()),
]

urlpatterns += router.urls