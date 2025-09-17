# Mooibanana - Dating App

A Django-based dating application with comprehensive features for user matching, chat, payments, and rewards system.

## Features

- **User Authentication**: Custom user registration and login system
- **Profile Management**: Complete user profiles with photo uploads
- **Matching System**: Like/dislike functionality with mutual matching
- **Real-time Chat**: Chat system for matched users
- **Payment Integration**: Stripe integration for premium features
- **Rewards System**: Points and rewards for user engagement
- **Notifications**: Real-time notifications for matches and messages
- **Admin Dashboard**: Comprehensive admin panel for user management

## Tech Stack

- **Backend**: Django 5.2.6
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Frontend**: Bootstrap 5, Crispy Forms
- **Payment**: Stripe API
- **Deployment**: Docker, Render
- **Performance**: Redis caching, Database optimization

## Project Structure

```
mooibanana_project/
├── accounts/           # User authentication and management
├── profiles/           # User profiles and discovery
├── likes/             # Like/dislike functionality
├── chat/              # Messaging system
├── payments/          # Payment processing
├── rewards/           # Rewards and points system
├── notifications/     # Notification system
├── admin_dashboard/   # Admin interface
├── templates/         # HTML templates
├── static/           # Static files (CSS, JS, images)
├── media/            # User uploaded files
└── mooibanana_project/ # Main project settings
```

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mooibanana_project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3
   PAYSTACK_PUBLIC_KEY=your-paystack-public-key
   PAYSTACK_SECRET_KEY=your-paystack-secret-key
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Docker Deployment

1. **Build Docker image**
   ```bash
   docker build -t mooibanana .
   ```

2. **Run container**
   ```bash
   docker run -p 8000:8000 mooibanana
   ```

### Production Deployment (Render)

1. **Environment Variables**
   Set the following environment variables in Render:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   SECRET_KEY=your-production-secret-key
   DEBUG=False
   PAYSTACK_PUBLIC_KEY=your-paystack-public-key
   PAYSTACK_SECRET_KEY=your-paystack-secret-key
   ```

2. **Deploy**
   Connect your repository to Render and deploy automatically.

## Usage

### User Features

- **Registration**: Sign up with email and basic information
- **Profile Creation**: Complete profile with photos and preferences
- **Discovery**: Browse and like/dislike other users
- **Matching**: Get notified when someone likes you back
- **Chat**: Message your matches
- **Payments**: Purchase premium features and gifts
- **Rewards**: Earn points for daily activities

### Admin Features

- **User Management**: View and manage all users
- **Analytics**: View platform statistics
- **Content Moderation**: Manage reported content
- **Payment Tracking**: Monitor transactions

## API Endpoints

### Authentication
- `POST /accounts/register/` - User registration
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout

### Profiles
- `GET /profiles/discover/` - Browse profiles
- `GET /profiles/my-profile/` - View own profile
- `POST /profiles/edit/` - Edit profile

### Likes & Matching
- `POST /likes/like/` - Like a profile
- `GET /likes/matches/` - View matches

### Chat
- `GET /chat/` - List conversations
- `GET /chat/room/<int:id>/` - Chat room

### Payments
- `GET /payments/packages/` - View packages
- `POST /payments/purchase/` - Process payment

## Management Commands

```bash
# Create test data
python manage.py create_test_match

# Create payment packages
python manage.py create_packages

# Performance optimization
python manage.py optimize_performance
```

## Configuration

### Database
The app supports both SQLite (development) and PostgreSQL (production) through the `DATABASE_URL` environment variable.

### Payment Processing
Stripe integration for handling payments. Configure your Stripe keys in environment variables.

### Performance Optimizations
- Database connection pooling
- Session caching
- Static file optimization
- Conditional GET middleware
- GZip compression

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Security

- CSRF protection enabled
- Secure password validation
- User input sanitization
- File upload restrictions
- Environment-based configuration

## License

This project is proprietary software. All rights reserved.

## Support

For support and questions, please contact the development team.