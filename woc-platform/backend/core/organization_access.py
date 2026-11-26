"""Authorization metadata; identity/provider verification remains elsewhere."""
from rest_framework.permissions import BasePermission
from .models import CollegeMembership, CompanyMembership, MembershipStatus, OrganizationStatus


def is_super_admin(user):
 return bool(user and user.is_authenticated and user.is_active and (
  user.is_superuser or (user.groups.filter(name='super_admin').exists() and user.has_perm('core.manage_organizations'))))


def active_colleges(user,role=None):
 if not user or not user.is_authenticated or not user.is_active: return CollegeMembership.objects.none()
 queryset=CollegeMembership.objects.filter(user=user,status=MembershipStatus.ACTIVE,institution__approval_status=OrganizationStatus.APPROVED)
 return queryset.filter(role=role) if role else queryset


def active_companies(user):
 if not user or not user.is_authenticated or not user.is_active: return CompanyMembership.objects.none()
 return CompanyMembership.objects.filter(user=user,role=CompanyMembership.Role.ADMIN,status=MembershipStatus.ACTIVE,company__approval_status=OrganizationStatus.APPROVED)


def access_context(user):
 if not user or not user.is_authenticated or not user.is_active:
  return {'roles':[],'permissions':[],'college_memberships':[],'company_memberships':[],'dashboard_url':None}
 roles=[];permissions=[]
 # A student is a baseline account, never a source of organization privileges.
 if user.groups.filter(name='student').exists() or (hasattr(user,'profile') and isinstance(user.profile.roles,list) and 'student' in user.profile.roles):
  roles.append('student');permissions.append('student.manage_self')
 colleges=list(user.college_memberships.select_related('institution').order_by('pk'))
 companies=list(user.company_memberships.select_related('company').order_by('pk'))
 if active_colleges(user,CollegeMembership.Role.ADMIN).exists():
  roles.append('college_admin');permissions.append('college.read_own')
 if active_companies(user).exists():
  roles.append('company_admin');permissions.append('company.read_own')
 if is_super_admin(user):
  roles.append('super_admin');permissions.append('organizations.manage')
 return {
  'roles':roles,'permissions':permissions,
  'college_memberships':[{'id':m.pk,'college_id':m.institution_id,'college_name':m.institution.name,'role':m.role,'membership_status':m.status,'organization_status':m.institution.approval_status} for m in colleges],
  'company_memberships':[{'id':m.pk,'company_id':str(m.company_id),'company_name':m.company.name,'role':m.role,'membership_status':m.status,'organization_status':m.company.approval_status} for m in companies],
  # Phase 2 & 3 role-based dashboard destination
  'dashboard_url':'/super-admin/' if is_super_admin(user) else ('/company/' if active_companies(user).exists() else ('/college/' if active_colleges(user,CollegeMembership.Role.ADMIN).exists() else ('/onboarding/' if any(m.status == MembershipStatus.PENDING or m.company.approval_status != OrganizationStatus.APPROVED for m in companies) or any(m.role == CollegeMembership.Role.ADMIN and (m.status == MembershipStatus.PENDING or m.institution.approval_status != OrganizationStatus.APPROVED) for m in colleges) else '/dashboard/'))),
 }


class IsPlatformSuperAdmin(BasePermission):
 def has_permission(self,request,view): return is_super_admin(request.user)


class IsCollegeAdministrator(BasePermission):
 def has_permission(self,request,view):
  return is_super_admin(request.user) or active_colleges(request.user,CollegeMembership.Role.ADMIN).exists()
 def has_object_permission(self,request,view,obj):
  return is_super_admin(request.user) or active_colleges(request.user,CollegeMembership.Role.ADMIN).filter(institution=obj).exists()


class IsCompanyAdministrator(BasePermission):
 def has_permission(self,request,view): return is_super_admin(request.user) or active_companies(request.user).exists()
 def has_object_permission(self,request,view,obj):
  return is_super_admin(request.user) or active_companies(request.user).filter(company=obj).exists()
