# Generated manually to increase otp_secret field size

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_add_2fa_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='otp_secret',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
