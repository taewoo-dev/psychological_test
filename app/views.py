import json

from django.urls import reverse
from django.utils import timezone

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from app.models import Participant, Question, Quiz


# Create your views here.
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "app/index.html")


@require_POST
@csrf_exempt
def add_participant(request: HttpRequest):
    data = json.loads(request.body)
    print(data)
    new_participant = Participant(
        name=data["name"],
        age=data["age"],
        gender=data["gender"],
        created_at=timezone.now()
    )
    new_participant.save()
    return JsonResponse({
        "redirect": "/quiz/",  # 장고의 URL 설정에 따라 경로를 조정합니다
        "participant_id": new_participant.id
    })


def quiz(request: HttpRequest):
    # 참여자 ID 쿠키를 가져옵니다.
    participant_id = request.COOKIES.get("participant_id")
    if not participant_id:
        # 참여자 ID가 없으면, 홈페이지로 리다이렉션합니다.
        return redirect('home')

    # 질문 목록을 가져옵니다.
    questions = Question.objects.all()
    questions_list = [question.content for question in questions]
    print(questions_list)

    # 퀴즈 페이지를 렌더링합니다.
    return render(request, 'app/quiz.html', {'questions': questions_list})


def get_questions(request):
    questions = Question.objects.filter(is_active=True).order_by('order_num')

    questions_list = [
        {
            "id": question.id,
            "content": question.content,
            "order_num": question.order_num,
        }
        for question in questions
    ]
    return JsonResponse({"questions": questions_list})


import pandas as pd
import plotly.express as px
import plotly.utils


def show_results(request):
    # 데이터베이스에서 데이터 조회
    participants_query = Participant.objects.all()
    quizzes_query = Quiz.objects.select_related('participant_id', 'question_id').all()

    print("여기",quizzes_query)
    # pandas DataFrame으로 변환
    participants_data = [
        {"age": participant.age, "gender": participant.gender}
        for participant in participants_query
    ]
    quizzes_data = [
        {
            "question_id": quiz.question_id.id,
            "chosen_answer": quiz.chosen_answer,
            "participant_age": quiz.participant_id.age,
        }
        for quiz in quizzes_query
    ]

    participants_df = pd.DataFrame(participants_data)
    quizzes_df = pd.DataFrame(quizzes_data)

    # Plotly 시각화 생성
    # 예시 1: 나이별 분포 (도넛 차트)
    fig_age = px.pie(
        participants_df,
        names="age",
        hole=0.3,
        title="Age Distribution",
        color_discrete_sequence=px.colors.sequential.RdBu,
        labels={"age": "Age Group"},
    )
    fig_age.update_traces(textposition="inside", textinfo="percent+label")

    fig_gender = px.pie(
        participants_df,
        names="gender",
        hole=0.3,
        title="Gender Distribution",
        color_discrete_sequence=px.colors.sequential.Purp,
        labels={"gender": "Gender"},
    )
    fig_gender.update_traces(textposition="inside", textinfo="percent+label")

    quiz_response_figs = {}

    # 각 질문 ID별로 반복하여 그래프 생성
    for question_id in quizzes_df["question_id"].unique():
        filtered_df = quizzes_df[quizzes_df["question_id"] == question_id]
        fig = px.histogram(
            filtered_df,
            x="chosen_answer",
            title=f"Question {question_id} Responses",
            color="chosen_answer",
            barmode="group",
            category_orders={"chosen_answer": ["yes", "no"]},  # 카테고리 순서 지정
            color_discrete_map={"yes": "RebeccaPurple", "no": "LightSeaGreen"},
        )  # 컬러 매핑
        fig.update_layout(
            xaxis_title="Chosen Answer",
            yaxis_title="Count",
            plot_bgcolor="rgba(0,0,0,0)",  # 배경색 투명
            paper_bgcolor="rgba(0,0,0,0)",  # 전체 배경색 투명
            font=dict(family="Courier New, monospace", size=18, color="#7f7f7f"),
            title_font=dict(
                family="Helvetica, Arial, sans-serif", size=22, color="RebeccaPurple"
            ),
        )
        fig.update_traces(marker_line_width=1.5, opacity=0.6)  # 투명도와 테두리 두께 조정

        # 생성된 그래프를 딕셔너리에 저장
        quiz_response_figs[f"question_{question_id}"] = fig

    age_quiz_response_figs = {}

    # 나이대를 구분하는 함수
    def age_group(age):
        if age == 'teenage':
            return "10s"
        elif age == 'twenty':
            return "20s"
        elif age == 'thirty':
            return "30s"
        elif age == 'forty':
            return "40s"
        elif age == 'fifties':
            return "50s"
        else:
            return "60s+"

    # 나이대 그룹 열 추가
    quizzes_df["age_group"] = quizzes_df["participant_age"].apply(age_group)

    # 각 질문 ID와 나이대별로 대답 분포를 시각화
    for question_id in quizzes_df["question_id"].unique():
        filtered_df = quizzes_df[quizzes_df["question_id"] == question_id]
        fig = px.histogram(
            filtered_df,
            x="age_group",
            color="chosen_answer",
            barmode="group",
            title=f"Question {question_id} Responses by Age Group",
            labels={"age_group": "Age Group", "chosen_answer": "Chosen Answer"},
            category_orders={"age_group": ["10s", "20s", "30s", "40s", "50s+"]},
        )

        # 스타일 조정
        fig.update_layout(
            xaxis_title="Age Group",
            yaxis_title="Count",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Courier New, monospace", size=18, color="#7f7f7f"),
            title_font=dict(
                family="Helvetica, Arial, sans-serif", size=22, color="RebeccaPurple"
            ),
        )
        fig.update_traces(marker_line_width=1.5, opacity=0.6)
        age_quiz_response_figs[f"question_{question_id}"] = fig

    # 딕셔너리에 저장된 그래프들을 JSON으로 변환
    graphs_json = json.dumps(
        {
            "age_distribution": fig_age,
            "gender_distribution": fig_gender,
            "quiz_responses": quiz_response_figs,
            "age_quiz_response_figs": age_quiz_response_figs,
        },
        cls=plotly.utils.PlotlyJSONEncoder,
    )

    # 데이터를 results.html에 전달
    return render(request, "app/results.html", {"graphs_json": graphs_json})


@csrf_exempt
@require_POST
def submit(request):
    # 참여자 ID가 필요합니다.
    participant_id = request.COOKIES.get("participant_id")
    if not participant_id:
        return JsonResponse({"error": "Participant ID not found"}, status=400)

    data = json.loads(request.body)
    quizzes = data.get("quizzes", [])

    print(quizzes)

    for quiz in quizzes:
        question_id = quiz.get("question_id")
        chosen_answer = quiz.get("chosen_answer")
        participant = Participant.objects.get(id=participant_id)
        question = Question.objects.get(id=question_id)
        print(participant)
        print(question)
        # 새 Quiz 인스턴스 생성
        new_quiz_entry = Quiz(
            participant_id=participant,
            question_id=question,
            chosen_answer=chosen_answer,
        )
        # 데이터베이스에 추가
        new_quiz_entry.save()

    return JsonResponse(
        {
            "message": "Quiz answers submitted successfully.",
            "redirect": reverse("show_results"),
        }
    )
