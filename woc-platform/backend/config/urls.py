from django.contrib import admin
from django.urls import path
from core import views as v
from django_otp.admin import OTPAdminSite
admin.site.__class__=OTPAdminSite
urlpatterns=[path('admin/',admin.site.urls),path('api/health/',v.health),path('api/csrf/',v.csrf),path('api/register/',v.register),path('api/login/',v.sign_in),path('api/verify/',v.verify),path('api/logout/',v.sign_out),path('api/me/',v.me),path('api/programs/',v.catalogue),path('api/records/',v.records),path('api/learning/<uuid:pk>/',v.learning),path('api/notifications/',v.notifications),path('api/enquiries/',v.enquiry),path('api/admin/records/',v.admin_records),path('api/certificates/<uuid:pk>/',v.certificate)]
