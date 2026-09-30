from rest_framework.permissions import BasePermission


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'teacher'


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'student'


class IsParent(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'parent'