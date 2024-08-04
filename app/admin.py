from django.contrib import admin
from app.models import Participant, Admin, Question, Quiz
# Register your models here.

admin.site.register(Participant)
admin.site.register(Question)
admin.site.register(Quiz)
