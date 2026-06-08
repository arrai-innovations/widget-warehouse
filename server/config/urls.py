from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from vueda.info.urls import urlpatterns as vueda_info_urls
from vueda.user.urls import urlpatterns as vueda_user_urls
from vueda.user.views import VuedaForgotPasswordView, VuedaResetPasswordView
from vueda.workflow.urls import urlpatterns as vueda_workflow_urls

urlpatterns = [
    path(
        "routes/",
        include(
            [
                path("", include(vueda_info_urls)),
                path("", include(vueda_user_urls)),
                path("forgot-password/", VuedaForgotPasswordView.as_view(), name="forgot_password"),
                path("reset-password/", VuedaResetPasswordView.as_view(), name="reset_password"),
                *vueda_workflow_urls,
                path("", include("widget_warehouse.urls")),
            ]
        ),
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
