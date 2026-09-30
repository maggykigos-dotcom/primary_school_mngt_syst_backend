from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )
    # def get_permissions(self):

    # if self.action in ['create', 'update', 'partial_update', 'destroy']:
    #     return [IsAdmin()]

    # return [IsAuthenticated()]

class IsParent(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'parent'
        )


class IsStudent(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'student'
        )