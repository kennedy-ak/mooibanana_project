# Generated manually for city field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_add_school_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='city',
            field=models.CharField(blank=True, help_text='Your city', max_length=100),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['city'], name='profiles_pr_city_idx'),
        ),
    ]
