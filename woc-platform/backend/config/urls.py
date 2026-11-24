from django.contrib import admin
from django.urls import path
from core import views as v
from django_otp.admin import OTPAdminSite
admin.site.__class__=OTPAdminSite
urlpatterns=[
 path('admin/',admin.site.urls),
 path('api/health/',v.health),
 path('api/csrf/',v.csrf),
 path('api/register/',v.register),
 path('api/login/',v.sign_in),
 path('api/verify/',v.verify),
 path('api/resend-verification/',v.resend_verification),
 path('api/phone/send-otp/',v.send_phone_otp),
 path('api/auth/phone/',v.phone_auth),
 path('api/phone/verify-otp/',v.verify_phone_otp),
 path('api/phone/resend-otp/',v.resend_phone_otp),
 path('api/auth/google/url/',v.google_auth_url),
 path('api/auth/google/',v.google_auth),
 path('api/password-reset/request/',v.request_password_reset),
 path('api/password-reset/confirm/',v.confirm_password_reset),
 path('api/logout/',v.sign_out),
 path('api/me/',v.me),
 path('api/programs/',v.catalogue),
 path('api/records/',v.records),
 path('api/learning/<uuid:pk>/',v.learning),
 path('api/notifications/',v.notifications),
 path('api/enquiries/',v.enquiry),
 path('api/admin/records/',v.admin_records),
 path('api/certificates/<uuid:pk>/',v.certificate)
]
