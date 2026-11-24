from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('core', '0002_emaildeliverylog_phoneotpchallenge_and_more')]
    operations = [
        migrations.AddField(model_name='phoneotpchallenge', name='purpose', field=models.CharField(default='verification', max_length=20)),
        migrations.AddField(model_name='phoneotpchallenge', name='user', field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        migrations.AddConstraint(model_name='profile', constraint=models.UniqueConstraint(fields=('phone_number',), condition=~models.Q(phone_number=''), name='unique_profile_phone')),
    ]
