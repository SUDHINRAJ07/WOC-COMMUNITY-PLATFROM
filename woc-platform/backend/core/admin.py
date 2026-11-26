from django.contrib import admin
from .models import (
 Profile,Institution,Program,Record,Certificate,Notification,Enquiry,AuditLog,Match,
 OAuthIdentity,PhoneOTPChallenge,EmailOTPChallenge,PasswordResetToken,AuthAuditLog,EmailDeliveryLog,
 Company,CollegeMembership,CompanyMembership,Opportunity,
 TrainingBatch,CampusPlacement,CollegePartnership,
 SavedOpportunity,OpportunityApplicationLog,
 CampusEvent,EventRegistration,StudentClub,ClubMembership,CampusLeadership,CampusAnnouncement
)
for model in [Profile,Program,Record,Certificate,Notification,Enquiry,AuditLog,Match,OAuthIdentity,PhoneOTPChallenge,EmailOTPChallenge,PasswordResetToken,AuthAuditLog,EmailDeliveryLog,SavedOpportunity,OpportunityApplicationLog,CampusEvent,EventRegistration,StudentClub,ClubMembership,CampusLeadership,CampusAnnouncement]:
 try: admin.site.register(model)
 except admin.sites.AlreadyRegistered: pass


class OrganizationFoundationAdmin(admin.ModelAdmin):
 """Inspection only in Phase 1; approval/editing workflows arrive in Phase 2."""
 def has_module_permission(self,request):
  from .organization_access import is_super_admin
  return is_super_admin(request.user)
 def has_view_permission(self,request,obj=None): return self.has_module_permission(request)
 def has_add_permission(self,request): return False
 def has_change_permission(self,request,obj=None): return False
 def has_delete_permission(self,request,obj=None): return False
 def get_readonly_fields(self,request,obj=None): return [field.name for field in self.model._meta.fields]


for model in [Institution,Company,CollegeMembership,CompanyMembership,Opportunity,TrainingBatch,CampusPlacement,CollegePartnership]:
 admin.site.register(model,OrganizationFoundationAdmin)
