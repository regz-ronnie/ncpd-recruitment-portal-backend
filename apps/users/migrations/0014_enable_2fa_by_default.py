# Generated manually to enable 2FA by default for existing users

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_alter_otp_secret_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='otp_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.RunSQL(
            "UPDATE users_user SET otp_enabled = TRUE WHERE otp_enabled = FALSE",
            reverse_sql="UPDATE users_user SET otp_enabled = FALSE WHERE otp_enabled = TRUE"
        ),
    ]
