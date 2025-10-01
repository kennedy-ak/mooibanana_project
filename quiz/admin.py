from django.contrib import admin
from .models import Question, Choice, UserQuizResponse, DailyQuiz

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 4
    fields = ['text', 'is_correct', 'order']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text_preview', 'category', 'difficulty', 'points_value', 'is_active', 'created_at']
    list_filter = ['category', 'difficulty', 'is_active', 'created_at']
    search_fields = ['text']
    inlines = [ChoiceInline]
    fields = ['text', 'category', 'difficulty', 'points_value', 'is_active', 'created_by']
    readonly_fields = ['created_by']
    
    def text_preview(self, obj):
        return f"{obj.text[:50]}..."
    text_preview.short_description = "Question"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'text', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__category']
    search_fields = ['text', 'question__text']
    
    def question_preview(self, obj):
        return f"{obj.question.text[:30]}..."
    question_preview.short_description = "Question"

@admin.register(UserQuizResponse)
class UserQuizResponseAdmin(admin.ModelAdmin):
    list_display = ['user', 'question_preview', 'is_correct', 'points_earned', 'answered_at']
    list_filter = ['is_correct', 'answered_at', 'question__category']
    search_fields = ['user__username', 'user__email', 'question__text']
    readonly_fields = ['user', 'question', 'selected_choice', 'is_correct', 'points_earned', 'answered_at']
    
    def question_preview(self, obj):
        return f"{obj.question.text[:30]}..."
    question_preview.short_description = "Question"
    
    def has_add_permission(self, request):
        return False

@admin.register(DailyQuiz)
class DailyQuizAdmin(admin.ModelAdmin):
    list_display = ['date', 'question_preview', 'total_responses', 'correct_responses', 'accuracy_percentage']
    list_filter = ['date', 'question__category']
    search_fields = ['question__text']
    fields = ['date', 'question', 'total_responses', 'correct_responses']
    readonly_fields = ['total_responses', 'correct_responses']
    
    def question_preview(self, obj):
        return f"{obj.question.text[:50]}..."
    question_preview.short_description = "Question"
