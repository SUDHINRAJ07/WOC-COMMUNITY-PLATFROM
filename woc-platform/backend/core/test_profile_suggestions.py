from django.contrib.auth.models import User
from django.test import TestCase
from django.core.cache import cache
from .models import Profile, ProfileSuggestion, Institution, CollegeMembership


class ProfileSuggestionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user=User.objects.create_user(username='suggestion-student',password=None)
        Profile.objects.create(user=self.user,age=21,roles=['student'])
        self.client.force_login(self.user)
        ProfileSuggestion.objects.bulk_create([
            ProfileSuggestion(kind='institution',source_id='C-TEST',name='Alpha College of Engineering',search_name='alpha college of engineering',state='Tamil Nadu',district='Chennai'),
            ProfileSuggestion(kind='city',source_id='city-test',name='Chennai',search_name='chennai madras',state='Tamil Nadu'),
            ProfileSuggestion(kind='state',source_id='state-test',name='Tamil Nadu',search_name='tamil nadu'),
            ProfileSuggestion(kind='skill',source_id='skill-test',name='Python',search_name='python'),
            ProfileSuggestion(kind='qualification',source_id='qualification-test',name='B.Tech Computer Science',search_name='b.tech computer science'),
        ])

    def test_college_search_and_no_approval_side_effects(self):
        response=self.client.get('/api/profile/suggestions/',{'kind':'institution','q':'ALPHA'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['results'][0]['name'],'Alpha College of Engineering')
        self.assertEqual(self.client.get('/api/profile/suggestions/',{'kind':'institution','q':'a'}).json()['results'],[])
        self.assertFalse(Institution.objects.exists())
        self.assertFalse(CollegeMembership.objects.exists())

    def test_city_state_filter_and_alias(self):
        result=self.client.get('/api/profile/suggestions/',{'kind':'city','q':'madras','state':'Tamil Nadu'})
        self.assertEqual(result.json()['results'][0]['name'],'Chennai')
        self.assertEqual(self.client.get('/api/profile/suggestions/',{'kind':'city','q':'Chennai','state':'Gujarat'}).json()['results'],[])

    def test_permissions_and_result_limit(self):
        self.assertEqual(self.client.get('/api/profile/suggestions/',{'kind':'private'}).status_code,400)
        self.assertEqual(self.client.post('/api/profile/suggestions/',{}).status_code,405)
        ProfileSuggestion.objects.bulk_create([ProfileSuggestion(kind='skill',source_id=f'extra-{i}',name=f'Python {i}',search_name=f'python {i}') for i in range(30)])
        self.assertEqual(len(self.client.get('/api/profile/suggestions/',{'kind':'skill','q':'py'}).json()['results']),20)
        self.client.logout()
        self.assertEqual(self.client.get('/api/profile/suggestions/',{'kind':'skill','q':'py'}).status_code,403)

    def test_profile_values_and_custom_tags_persist(self):
        response=self.client.patch('/api/student/profile/',{'city':'Chennai','state':'Tamil Nadu','institution':'Alpha College of Engineering','qualification':'B.Tech Computer Science','skills':['Python','Custom Research Skill'],'interests':['Information Technology','Marine Research']},content_type='application/json')
        self.assertEqual(response.status_code,200)
        profile=Profile.objects.get(user=self.user)
        self.assertEqual(profile.state,'Tamil Nadu')
        self.assertEqual(profile.skills,['Python','Custom Research Skill'])
        self.assertEqual(profile.interests,['Information Technology','Marine Research'])
        self.assertEqual(profile.roles,['student'])
        self.assertFalse(CollegeMembership.objects.exists())

    def test_education_dates_and_department(self):
        url='/api/student/profile/'
        result=self.client.patch(url,{'education_start_year':2024,'graduation_year':2028,'department':'Computer Science'},content_type='application/json')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()['user']['education_start_year'],2024)
        self.assertEqual(result.json()['user']['department'],'Computer Science')
        self.assertEqual(self.client.patch(url,{'graduation_year':2023},content_type='application/json').status_code,400)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.graduation_year,2028)

    def test_department_search(self):
        ProfileSuggestion.objects.create(kind='department',source_id='dept-test',name='Computer Science and Engineering',search_name='computer science and engineering')
        response=self.client.get('/api/profile/suggestions/',{'kind':'department','q':'computer'})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['results'][0]['name'],'Computer Science and Engineering')

    def test_personal_professional_fields(self):
        url='/api/student/profile/'
        response=self.client.patch(url,{'professional_headline':'CSE Student | Python Developer','languages':['Tamil','English',' tamil '],'current_status':'studying'},content_type='application/json')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['user']['languages'],['Tamil','English'])
        self.assertEqual(response.json()['user']['current_status'],'studying')
        self.assertEqual(self.client.get(url).json()['user']['professional_headline'],'CSE Student | Python Developer')
        self.assertEqual(self.client.patch(url,{'current_status':'superadmin'},content_type='application/json').status_code,400)
        self.assertEqual(self.client.patch(url,{'languages':['x'*61]},content_type='application/json').status_code,400)
        self.assertEqual(self.client.patch(url,{'professional_headline':'x'*161},content_type='application/json').status_code,400)

    def test_address_and_pin_code(self):
        url='/api/student/profile/'
        result=self.client.patch(url,{'address':'12 College Road','pin_code':'600001'},content_type='application/json')
        self.assertEqual(result.status_code,200)
        self.assertEqual(self.client.get(url).json()['user']['pin_code'],'600001')
        self.assertEqual(self.client.get(url).json()['user']['address'],'12 College Road')
        for pin in ['123','000001','ABCDEF','6000017']:
            self.assertEqual(self.client.patch(url,{'pin_code':pin},content_type='application/json').status_code,400)
        self.assertEqual(self.client.patch(url,{'pin_code':''},content_type='application/json').status_code,200)
