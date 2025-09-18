# Generated manually to populate referral codes

import secrets
import string
from django.db import migrations, models
import django.db.models.deletion


def generate_referral_code():
    """Generate a unique 8-character referral code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def populate_referral_codes(apps, schema_editor):
    """Populate empty referral codes with unique values"""
    CustomUser = apps.get_model('accounts', 'CustomUser')
    
    # Get all users with empty or None referral codes
    users_without_codes = CustomUser.objects.filter(
        models.Q(referral_code__isnull=True) | models.Q(referral_code='')
    )
    
    existing_codes = set(
        CustomUser.objects.exclude(
            models.Q(referral_code__isnull=True) | models.Q(referral_code='')
        ).values_list('referral_code', flat=True)
    )
    
    for user in users_without_codes:
        # Generate a unique code
        while True:
            code = generate_referral_code()
            if code not in existing_codes:
                existing_codes.add(code)
                user.referral_code = code
                break
        
        user.save(update_fields=['referral_code'])


def reverse_populate_referral_codes(apps, schema_editor):
    """Reverse migration - set all referral codes to empty"""
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.all().update(referral_code='')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_customuser_super_likes_balance'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='referral_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='customuser',
            name='referral_points_earned',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='customuser',
            name='referred_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to='accounts.CustomUser'),
        ),
        migrations.RunPython(
            populate_referral_codes,
            reverse_populate_referral_codes,
        ),
    ]