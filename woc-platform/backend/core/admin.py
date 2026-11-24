from django.contrib import admin
from .models import (
 Profile,Institution,Program,Record,Certificate,Notification,Enquiry,AuditLog,Match,
 OAuthIdentity,PhoneOTPChallenge,PasswordResetToken,AuthAuditLog,EmailDeliveryLog
)
for model in [Profile,Institution,Program,Record,Certificate,Notification,Enquiry,AuditLog,Match,OAuthIdentity,PhoneOTPChallenge,PasswordResetToken,AuthAuditLog,EmailDeliveryLog]:
 try: admin.site.register(model)
 except admin.sites.AlreadyRegistered: pass
