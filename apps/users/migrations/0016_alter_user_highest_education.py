# Generated manually to add default value to highest_education

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_alter_certification_user_alter_profile_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='highest_education',
            field=models.CharField(
                blank=True,
                choices=[
                    ('high_school', 'High School'),
                    ('diploma', 'Diploma'),
                    ('bachelor', 'Bachelor Degree'),
                    ('master', 'Master Degree'),
                    ('phd', 'PhD'),
                    ('professional_certification', 'Professional Certification'),
                    ('other', 'Other'),
                ],
                default='high_school',
                max_length=50,
                null=True
            ),
        ),
    ]
