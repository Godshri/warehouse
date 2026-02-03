from rest_framework import permissions


def _has_role(user, roles):
    return bool(user and user.is_authenticated and getattr(user, 'role', None) in roles)


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, {'admin'})


class IsStorekeeperOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, {'admin', 'storekeeper'})


class IsObserverOrAbove(permissions.BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, {'admin', 'storekeeper', 'observer'})


class ReadOnlyOrStorekeeper(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return _has_role(request.user, {'admin', 'storekeeper'})
