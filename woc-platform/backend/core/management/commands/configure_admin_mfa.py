from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice
from core.models import Profile
class Command(BaseCommand):
 help='Configure a pre-created administrator with a TOTP authenticator. Run interactively on your own machine.'
 def add_arguments(self,parser):parser.add_argument('username')
 def handle(self,*args,**options):
  try:u=User.objects.get(username=options['username'],is_staff=True)
  except User.DoesNotExist:raise CommandError('Create a staff account first using createsuperuser.')
  Profile.objects.get_or_create(user=u,defaults={'age':18,'email_verified':True,'roles':['super_admin']})
  d,created=TOTPDevice.objects.get_or_create(user=u,name='WOC admin',defaults={'confirmed':True})
  self.stdout.write('Add this private provisioning URI to your authenticator. Do not share it:')
  self.stdout.write(d.config_url)
