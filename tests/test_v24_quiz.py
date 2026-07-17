# -*- coding: utf-8 -*-
"""test_v24_quiz.py — v2.4 Phase 5 测验/考试测试"""

import os
import tempfile
import pytest

from webapp.backend.userstore import UserStore
from webapp.backend.quiz_content import (
    LESSON_QUIZZES, STAGE_EXAMS,
    get_lesson_quiz, grade_lesson_quiz,
    get_stage_exam, grade_stage_exam,
)


@pytest.fixture
def store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    s = UserStore(db_path=path)
    yield s
    try:
        os.unlink(path)
    except OSError:
        pass


class TestLessonQuizContent:
    def test_all_24_lessons_have_quiz(self):
        """24 课全部有测验"""
        assert len(LESSON_QUIZZES) == 24
        for cid, quiz in LESSON_QUIZZES.items():
            assert len(quiz) == 3, f"{cid} 应有 3 题"
            for q in quiz:
                assert 0 <= q["answer"] < len(q["options"])

    def test_get_quiz_hides_answer(self):
        quiz = get_lesson_quiz("ch01")
        assert len(quiz) == 3
        assert "answer" not in quiz[0]
        assert "question" in quiz[0]

    def test_grade_all_correct(self):
        quiz = LESSON_QUIZZES["ch01"]
        answers = [q["answer"] for q in quiz]
        result = grade_lesson_quiz("ch01", answers)
        assert result["score"] == 100
        assert result["correct_count"] == 3
        assert result["passed"] is True

    def test_grade_all_wrong(self):
        quiz = LESSON_QUIZZES["ch01"]
        answers = [(q["answer"] + 1) % len(q["options"]) for q in quiz]
        result = grade_lesson_quiz("ch01", answers)
        assert result["score"] == 0
        assert result["passed"] is False

    def test_grade_partial(self):
        quiz = LESSON_QUIZZES["ch01"]
        answers = [quiz[0]["answer"], 99, 99]  # 只对第 1 题
        result = grade_lesson_quiz("ch01", answers)
        assert result["correct_count"] == 1
        assert result["score"] == 33

    def test_unknown_chapter(self):
        result = grade_lesson_quiz("ch99", [0, 0, 0])
        assert "error" in result


class TestStageExamContent:
    def test_all_6_stages_have_exam(self):
        assert len(STAGE_EXAMS) == 6
        for sid, exam in STAGE_EXAMS.items():
            assert len(exam["questions"]) == 10, f"{sid} 应有 10 题"
            assert exam["pass_score"] == 80

    def test_get_exam_hides_answer(self):
        exam = get_stage_exam("stage1")
        assert "title" in exam
        assert len(exam["questions"]) == 10
        assert "answer" not in exam["questions"][0]

    def test_grade_exam_pass(self):
        exam = STAGE_EXAMS["stage1"]
        answers = [q["answer"] for q in exam["questions"]]
        result = grade_stage_exam("stage1", answers)
        assert result["score"] == 100
        assert result["passed"] is True

    def test_grade_exam_pass_boundary(self):
        """8/10 = 80 分，刚好通过"""
        exam = STAGE_EXAMS["stage1"]
        answers = [q["answer"] for q in exam["questions"]]
        # 错 2 题
        answers[0] = (answers[0] + 1) % 4
        answers[1] = (answers[1] + 1) % 4
        result = grade_stage_exam("stage1", answers)
        assert result["score"] == 80
        assert result["passed"] is True

    def test_grade_exam_fail(self):
        """7/10 = 70 分，不通过"""
        exam = STAGE_EXAMS["stage1"]
        answers = [q["answer"] for q in exam["questions"]]
        for i in range(3):
            answers[i] = (answers[i] + 1) % 4
        result = grade_stage_exam("stage1", answers)
        assert result["score"] == 70
        assert result["passed"] is False


class TestQuizPersistence:
    def test_quiz_result_saved(self, store):
        store.quiz_result_save("ch01", "lesson_quiz", 100, 3, 3, True)
        best = store.quiz_result_best("ch01")
        assert best["score"] == 100

    def test_certificates_only_passed(self, store):
        store.quiz_result_save("stage1", "stage_exam", 90, 9, 10, True)
        store.quiz_result_save("stage2", "stage_exam", 60, 6, 10, False)
        passed = store.quiz_results_passed("stage_exam")
        assert len(passed) == 1
        assert passed[0]["quiz_id"] == "stage1"
