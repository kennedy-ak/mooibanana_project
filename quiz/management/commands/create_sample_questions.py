from django.core.management.base import BaseCommand
from quiz.models import Question, Choice

class Command(BaseCommand):
    help = 'Create sample quiz questions for testing'

    def handle(self, *args, **options):
        sample_questions = [
            {
                'text': 'What is the capital of France?',
                'category': 'geography',
                'difficulty': 'easy',
                'points_value': 1,
                'choices': [
                    {'text': 'London', 'is_correct': False},
                    {'text': 'Berlin', 'is_correct': False},
                    {'text': 'Paris', 'is_correct': True},
                    {'text': 'Madrid', 'is_correct': False},
                ]
            },
            {
                'text': 'Who painted the Mona Lisa?',
                'category': 'entertainment',
                'difficulty': 'medium',
                'points_value': 2,
                'choices': [
                    {'text': 'Vincent van Gogh', 'is_correct': False},
                    {'text': 'Leonardo da Vinci', 'is_correct': True},
                    {'text': 'Pablo Picasso', 'is_correct': False},
                    {'text': 'Michelangelo', 'is_correct': False},
                ]
            },
            {
                'text': 'What is the largest planet in our solar system?',
                'category': 'science',
                'difficulty': 'easy',
                'points_value': 1,
                'choices': [
                    {'text': 'Earth', 'is_correct': False},
                    {'text': 'Saturn', 'is_correct': False},
                    {'text': 'Jupiter', 'is_correct': True},
                    {'text': 'Mars', 'is_correct': False},
                ]
            },
            {
                'text': 'In which year did World War II end?',
                'category': 'history',
                'difficulty': 'medium',
                'points_value': 2,
                'choices': [
                    {'text': '1944', 'is_correct': False},
                    {'text': '1945', 'is_correct': True},
                    {'text': '1946', 'is_correct': False},
                    {'text': '1947', 'is_correct': False},
                ]
            },
            {
                'text': 'What is the chemical symbol for gold?',
                'category': 'science',
                'difficulty': 'medium',
                'points_value': 2,
                'choices': [
                    {'text': 'Go', 'is_correct': False},
                    {'text': 'Gd', 'is_correct': False},
                    {'text': 'Au', 'is_correct': True},
                    {'text': 'Ag', 'is_correct': False},
                ]
            },
            {
                'text': 'Which programming language is known as the "language of the web"?',
                'category': 'technology',
                'difficulty': 'easy',
                'points_value': 1,
                'choices': [
                    {'text': 'Python', 'is_correct': False},
                    {'text': 'Java', 'is_correct': False},
                    {'text': 'JavaScript', 'is_correct': True},
                    {'text': 'C++', 'is_correct': False},
                ]
            },
            {
                'text': 'What is the fastest land animal?',
                'category': 'general',
                'difficulty': 'easy',
                'points_value': 1,
                'choices': [
                    {'text': 'Lion', 'is_correct': False},
                    {'text': 'Cheetah', 'is_correct': True},
                    {'text': 'Leopard', 'is_correct': False},
                    {'text': 'Tiger', 'is_correct': False},
                ]
            },
            {
                'text': 'Who wrote the novel "1984"?',
                'category': 'literature',
                'difficulty': 'medium',
                'points_value': 2,
                'choices': [
                    {'text': 'Aldous Huxley', 'is_correct': False},
                    {'text': 'George Orwell', 'is_correct': True},
                    {'text': 'Ray Bradbury', 'is_correct': False},
                    {'text': 'Kurt Vonnegut', 'is_correct': False},
                ]
            },
            {
                'text': 'In tennis, what does the term "love" mean?',
                'category': 'sports',
                'difficulty': 'easy',
                'points_value': 1,
                'choices': [
                    {'text': 'A perfect serve', 'is_correct': False},
                    {'text': 'Zero points', 'is_correct': True},
                    {'text': 'A tie game', 'is_correct': False},
                    {'text': 'Match point', 'is_correct': False},
                ]
            },
            {
                'text': 'What is the square root of 144?',
                'category': 'general',
                'difficulty': 'easy',
                'points_value': 1,
                'choices': [
                    {'text': '10', 'is_correct': False},
                    {'text': '11', 'is_correct': False},
                    {'text': '12', 'is_correct': True},
                    {'text': '13', 'is_correct': False},
                ]
            }
        ]

        created_count = 0
        for question_data in sample_questions:
            question, created = Question.objects.get_or_create(
                text=question_data['text'],
                defaults={
                    'category': question_data['category'],
                    'difficulty': question_data['difficulty'],
                    'points_value': question_data['points_value'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created question: {question.text[:50]}...")
                
                # Create choices
                for i, choice_data in enumerate(question_data['choices']):
                    Choice.objects.create(
                        question=question,
                        text=choice_data['text'],
                        is_correct=choice_data['is_correct'],
                        order=i + 1
                    )
            else:
                self.stdout.write(f"Question already exists: {question.text[:50]}...")

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample questions')
        )