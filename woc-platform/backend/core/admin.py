from django.contrib import admin
from .models import Profile,Institution,Program,Record,Certificate,Notification,Enquiry,AuditLog,Match
for model in [Profile,Institution,Program,Record,Certificate,Notification,Enquiry,AuditLog,Match]: admin.site.register(model)
