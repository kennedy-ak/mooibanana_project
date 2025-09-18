# Generated manually for unlikes in packages

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='likepackage',
            name='unlikes',
            field=models.IntegerField(default=0),
        ),
    ]
