# Generated manually for ProfilePhoto order field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_profile_profiles_pr_is_comp_a5aa2d_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profilephoto',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='profilephoto',
            options={'ordering': ['order', 'uploaded_at']},
        ),
    ]
