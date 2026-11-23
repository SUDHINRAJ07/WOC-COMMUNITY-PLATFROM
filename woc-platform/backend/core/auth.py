from rest_framework.authentication import SessionAuthentication

class CsrfSessionAuthentication(SessionAuthentication):
 """Require CSRF on anonymous writes as well as authenticated session requests."""
 def authenticate(self,request):
  if request.method not in ('GET','HEAD','OPTIONS','TRACE'):
   self.enforce_csrf(request)
  return super().authenticate(request)
