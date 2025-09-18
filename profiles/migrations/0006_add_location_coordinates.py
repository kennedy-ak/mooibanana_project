# Generated manually for latitude and longitude fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0005_add_city_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Latitude for location-based matching', max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Longitude for location-based matching', max_digits=9, null=True),
        ),
    ]
