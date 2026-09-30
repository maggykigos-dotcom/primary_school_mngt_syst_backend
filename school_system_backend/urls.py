from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def home(request):
    return redirect("/admin/")


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),

    # Authentication
    path("api/auth/", include("accounts.urls")),

    # Academics
    path("api/academics/", include("academics.urls")),

    # Finance
    path("api/finance/", include("finance.urls")),

    # Communication
    path("api/communication/", include("communication.urls")),
]


# Serve uploaded media files during development
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT,
)


# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from django.shortcuts import redirect


# def home(request):
#     return redirect('/admin/')


# urlpatterns = [
#     path('', home),
#     path('admin/', admin.site.urls),

#     path('api/auth/', include('accounts.urls')),
#     path('api/academics/', include('academics.urls')),
#     path('api/finance/', include('finance.urls')),
#     path('api/communication/', include('communication.urls')),
# ]

# urlpatterns += static(
#     settings.MEDIA_URL,
#     document_root=settings.MEDIA_ROOT
# )

# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from django.shortcuts import redirect



# def home(request):
#     return redirect('/admin/')  

# urlpatterns = [
#     path('', home),
#     path('admin/', admin.site.urls),

#     path('api/auth/', include('accounts.urls')),
#     path('api/academics/', include('academics.urls')),
#     path('api/finance/', include('finance.urls')),
#     path('api/communication/', include('communication.urls')),
# ]

# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
