# Generated manually for unlikes balance

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_referral_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='unlikes_balance',
            field=models.IntegerField(default=0),
        ),
    ]
