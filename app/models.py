from django.db import models

# Create your models here.
from datetime import datetime

from django.utils import timezone


class Participant(models.Model):
    __tablename__ = "participant"

    name = models.CharField(max_length=50)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=timezone.now)


# class Admin(models.Model):
#     __tablename__ = "admin"
#
#     username = models.CharField(max_length=50)
#     password = models.CharField(max_length=50)


class Question(models.Model):
    __tablename__ = "question"

    content = models.CharField(max_length=255)
    order_num = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)


class Quiz(models.Model):
    __tablename__ = "quiz"

    participant_id = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="quizzes")
    question_id = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="quizzes")
    chosen_answer = models.CharField(max_length=255)

