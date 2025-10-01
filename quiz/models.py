from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General Knowledge'),
        ('science', 'Science'),
        ('history', 'History'),
        ('sports', 'Sports'),
        ('entertainment', 'Entertainment'),
        ('geography', 'Geography'),
        ('literature', 'Literature'),
        ('technology', 'Technology'),
    ]
    
    text = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    points_value = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.text[:50]}..."

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ['question', 'order']
    
    def __str__(self):
        return f"{self.question.text[:30]}... - {self.text}"

class UserQuizResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_responses')
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    points_earned = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'question']
        ordering = ['-answered_at']
    
    def save(self, *args, **kwargs):
        self.is_correct = self.selected_choice.is_correct
        if self.is_correct:
            self.points_earned = self.question.points_value
            self.user.points_balance += self.points_earned
            self.user.save()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.question.text[:30]}... - {'Correct' if self.is_correct else 'Incorrect'}"

class DailyQuiz(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    date = models.DateField(unique=True)
    total_responses = models.IntegerField(default=0)
    correct_responses = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Daily Quizzes"
    
    @property
    def accuracy_percentage(self):
        if self.total_responses == 0:
            return 0
        return round((self.correct_responses / self.total_responses) * 100, 2)
    
    def __str__(self):
        return f"Daily Quiz - {self.date} - {self.question.text[:30]}..."
