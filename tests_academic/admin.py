from django.contrib import admin

from .models import Answer, Question, Result, StudentAnswer, Test


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "duration", "passing_score", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "test", "order")
    list_filter = ("test",)
    inlines = [AnswerInline]


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "test", "score", "passed", "submitted_at")
    list_filter = ("passed", "test")
    search_fields = ("student__username", "test__name")


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("student", "question", "answer", "answered_at")
    list_filter = ("question__test",)
    search_fields = ("student__username", "question__text", "answer__text")
