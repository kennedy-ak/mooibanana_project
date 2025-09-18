# Generated manually for school_name field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_profilephoto_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='school_name',
            field=models.CharField(blank=True, help_text='Name of your school/university', max_length=200),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['school_name'], name='profiles_pr_school__idx'),
        ),
    ]
