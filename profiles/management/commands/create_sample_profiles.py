import random
import os
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.conf import settings
from profiles.models import Profile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create 20 sample profiles for testing'

    def create_default_profile_picture(self):
        """Create a simple default profile picture"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a simple colored circle as default profile picture
            size = (300, 300)
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD']
            color = random.choice(colors)
            
            # Create image with colored background
            img = Image.new('RGB', size, color)
            draw = ImageDraw.Draw(img)
            
            # Draw a circle
            margin = 30
            draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], fill='white', outline=color, width=5)
            
            # Save to bytes
            img_io = io.BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            
            return ContentFile(img_io.read(), name=f'default_profile_{random.randint(1000, 9999)}.png')
        except ImportError:
            # If PIL is not available, return None and skip profile picture
            return None

    def handle(self, *args, **options):
        # Sample data
        first_names = [
            'Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'Ethan', 'Sophia', 'Mason',
            'Isabella', 'William', 'Mia', 'James', 'Charlotte', 'Benjamin', 'Amelia',
            'Lucas', 'Harper', 'Henry', 'Evelyn', 'Alexander', 'Abigail', 'Michael',
            'Emily', 'Daniel', 'Sofia', 'Matthew', 'Avery', 'Jackson', 'Ella', 'Sebastian'
        ]
        
        last_names = [
            'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson',
            'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee',
            'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez',
            'Lewis', 'Robinson', 'Walker'
        ]

        universities = [
            'University of Amsterdam', 'Delft University of Technology', 'Utrecht University',
            'Wageningen University', 'Erasmus University Rotterdam', 'University of Groningen',
            'Leiden University', 'Maastricht University', 'VU Amsterdam', 'Eindhoven University of Technology'
        ]

        locations = [
            'Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht', 'Eindhoven', 'Tilburg',
            'Groningen', 'Almere', 'Breda', 'Nijmegen', 'Enschede', 'Haarlem',
            'Arnhem', 'Zaanstad', 'Amersfoort', 'Apeldoorn', 'Dordrecht', 'Leiden'
        ]

        interests_list = [
            'Photography', 'Traveling', 'Reading', 'Music', 'Cooking', 'Sports',
            'Gaming', 'Art', 'Dancing', 'Hiking', 'Movies', 'Fitness', 'Technology',
            'Fashion', 'Swimming', 'Cycling', 'Yoga', 'Writing', 'Languages',
            'Volunteering', 'Singing', 'Theatre', 'Gardening', 'Coffee', 'Wine',
            'Basketball', 'Soccer', 'Tennis', 'Rock climbing', 'Meditation'
        ]

        bio_templates = [
            "Love exploring new places and trying different cuisines. Always up for an adventure! 🌍",
            "Passionate about {interest1} and {interest2}. Looking for someone to share good times with ✨",
            "Student life is busy but I always make time for {interest1}. Coffee dates are my favorite ☕",
            "Big fan of {interest1} and {interest2}. Let's explore the city together! 🏙️",
            "When I'm not studying, you can find me {interest1} or {interest2}. Love meeting new people! 😊",
            "Studying {study} but my real passion is {interest1}. Always down for good conversations 💬",
            "Life's too short to be boring! Love {interest1}, {interest2}, and making memories 📸",
            "Future {study} professional with a love for {interest1}. Let's grab coffee sometime! ☕",
            "Believer in living life to the fullest. Passionate about {interest1} and {interest2} 🌟",
            "Always learning something new. Currently obsessed with {interest1} and {interest2} 📚"
        ]

        study_fields = ['computer_science', 'business', 'engineering', 'medicine', 'law', 'arts', 'psychology', 'other']
        study_field_names = {
            'computer_science': 'Computer Science',
            'business': 'Business',
            'engineering': 'Engineering',
            'medicine': 'Medicine',
            'law': 'Law',
            'arts': 'Arts',
            'psychology': 'Psychology',
            'other': 'Other'
        }

        created_count = 0
        
        for i in range(20):
            # Generate unique username and email
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(10, 99)}"
            email = f"{username}@student.uva.nl"
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                continue
                
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password='testpass123',
                is_student=True,
                university=random.choice(universities),
                student_id=f"STU{random.randint(100000, 999999)}",
                is_verified=True,
                likes_balance=random.randint(5, 50),
                super_likes_balance=random.randint(1, 10),
                points_balance=random.randint(0, 100)
            )
            
            # Generate age between 18-28
            age = random.randint(18, 28)
            birth_date = date.today() - timedelta(days=age*365 + random.randint(0, 365))
            
            # Select random interests
            selected_interests = random.sample(interests_list, random.randint(3, 6))
            interests_str = ', '.join(selected_interests)
            
            # Select study field and generate bio
            study_field = random.choice(study_fields)
            bio_template = random.choice(bio_templates)
            
            # Fill bio template with relevant data
            bio = bio_template.format(
                interest1=selected_interests[0] if len(selected_interests) > 0 else 'traveling',
                interest2=selected_interests[1] if len(selected_interests) > 1 else 'music',
                study=study_field_names[study_field]
            )
            
            # Create default profile picture
            default_picture = self.create_default_profile_picture()
            
            # Create profile
            profile = Profile.objects.create(
                user=user,
                bio=bio,
                birth_date=birth_date,
                study_field=study_field,
                study_year=random.randint(1, 4),
                interests=interests_str,
                location=random.choice(locations),
                profile_picture=default_picture
            )
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created profile for {user.first_name} {user.last_name} ({user.email})')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} sample profiles!')
        )
        self.stdout.write(
            self.style.WARNING('Note: Profile pictures need to be added manually or via separate command.')
        )