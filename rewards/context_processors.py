# rewards/context_processors.py
from django.utils import timezone
from .models import PrizeAnnouncement

def prize_announcements(request):
    """Make active prize announcements available to all templates"""
    now = timezone.now()

    # Get active prizes that are within their display date range (if set)
    active_prizes = PrizeAnnouncement.objects.filter(is_active=True)

    # Filter by date range if dates are set
    filtered_prizes = []
    for prize in active_prizes:
        if prize.start_date and prize.end_date:
            if prize.start_date <= now <= prize.end_date:
                filtered_prizes.append(prize)
        elif prize.start_date:
            if now >= prize.start_date:
                filtered_prizes.append(prize)
        elif prize.end_date:
            if now <= prize.end_date:
                filtered_prizes.append(prize)
        else:
            # No date restrictions, always show
            filtered_prizes.append(prize)

    return {
        'active_prizes': filtered_prizes
    }
