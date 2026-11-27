from urllib.parse import urlsplit
from django.db.models import Q
from .models import CampusEvent
from .organization_access import active_colleges,access_context


def notification_destination(notification):
    target=notification.target_url
    if target and not any(c in target for c in ['\\','\r','\n']) and target.startswith('/') and not target.startswith('//'):
        parsed=urlsplit(target)
        if parsed.path in ['/dashboard/','/college/','/company/','/super-admin/','/careers/','/careers/opportunity/','/academy/']:
            return target
    user=notification.user
    message=notification.message
    lower=message.lower()
    events=CampusEvent.objects.filter(Q(visibility='public')|Q(institution__in=active_colleges(user).values('institution_id'))).exclude(status='suspended').select_related('institution')
    for event in events:
        if event.title in message and event.institution.name in message:
            return f'/dashboard/?tab=engagement&event={event.pk}'
    for record in user.record_set.select_related('program').all():
        if record.program.title in message and any(word in lower for word in ['course','enrol','lesson','learning','assessment']):
            return f'/dashboard/?tab=learning&record={record.pk}'
    destination=access_context(user)['dashboard_url']
    if destination not in ['/dashboard/',None]:return destination
    if any(word in lower for word in ['event','club','leadership','announcement','workshop']):return '/dashboard/?tab=engagement'
    if any(word in lower for word in ['batch','training']):return '/dashboard/?tab=batches'
    if 'certificate' in lower:return '/dashboard/?tab=certificates'
    if any(word in lower for word in ['course','lesson','assessment','learning','academy']):return '/dashboard/?tab=learning'
    if any(word in lower for word in ['membership','affiliation','college']):return '/dashboard/?tab=college'
    if any(word in lower for word in ['opportunit','career','job','internship','application']):return '/careers/'
    return '/dashboard/?tab=profile'
