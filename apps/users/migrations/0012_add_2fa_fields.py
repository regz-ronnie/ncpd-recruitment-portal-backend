# Generated manually for 2FA fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_alter_profile_profile_picture_alter_user_resume_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='otp_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='otp_secret',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='otp_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='otp_backup_codes',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
