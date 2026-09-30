class PermissionService:

    @staticmethod
    def can_message(sender, receiver):

        if sender.role == "admin":
            return True

        if sender.role == "teacher":
            return receiver.role in ["student", "parent"]

        if sender.role == "parent":
            return receiver.role == "teacher"

        if sender.role == "student":
            return receiver.role == "teacher"

        return False
