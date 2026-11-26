from rest_framework import serializers
from urllib.parse import urlsplit


class StrictInputSerializer(serializers.Serializer):
 def to_internal_value(self,data):
  if not isinstance(data,dict): raise serializers.ValidationError('Expected an object.')
  unknown=set(data)-set(self.fields)
  if unknown: raise serializers.ValidationError({key:'This field cannot be supplied.' for key in sorted(unknown)})
  return super().to_internal_value(data)


class CollegeOnboardingSerializer(StrictInputSerializer):
 contact_phone=serializers.CharField(source="phone",max_length=30,required=False,allow_blank=True)
 state=serializers.CharField(max_length=100,required=False,allow_blank=True)
 registration_reference=serializers.CharField(max_length=200,required=False,allow_blank=True)
 name=serializers.CharField(max_length=200)
 city=serializers.CharField(max_length=100)
 website=serializers.URLField(max_length=500,required=False,allow_blank=True)
 contact_email=serializers.EmailField(max_length=254)
 address=serializers.CharField(max_length=2000,required=False,allow_blank=True)
 def validate_website(self,value):
  if value and not value.startswith('https://'): raise serializers.ValidationError('Use an HTTPS website URL.')
  if value and (urlsplit(value).username is not None or urlsplit(value).password is not None): raise serializers.ValidationError('Website URLs cannot contain credentials.')
  return value


class CompanyOnboardingSerializer(CollegeOnboardingSerializer):
 contact_phone=serializers.CharField(max_length=30,required=False,allow_blank=True)
 city=serializers.CharField(max_length=100,required=False,allow_blank=True)
 website=serializers.URLField(max_length=500,required=False,allow_blank=True)
 address=serializers.CharField(max_length=2000,required=False,allow_blank=True)
 company_type=serializers.CharField(max_length=100,required=False,allow_blank=True)
 cin=serializers.RegexField(r"^[A-Za-z0-9]{21}$",required=False,allow_blank=True,max_length=21)
 pin_code=serializers.RegexField(r"^[0-9]{6}$",required=False,allow_blank=True,max_length=6)
 designation=serializers.CharField(max_length=150,required=False,allow_blank=True)
 industry=serializers.CharField(max_length=100,required=False,allow_blank=True)
 company_size=serializers.CharField(max_length=50,required=False,allow_blank=True)
 contact_person=serializers.CharField(max_length=150,required=False,allow_blank=True)
 recruitment_email=serializers.EmailField(required=False,allow_blank=True)
 description=serializers.CharField(max_length=2000,required=False,allow_blank=True)
