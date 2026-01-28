"""
LLM-based explanation evaluation service.
"""
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.core.config import settings


@dataclass
class ExplanationEvaluation:
    score: int
    passed: bool
    feedback: str
    breakdown: Dict[str, int]


class ExplanationEvalService:
    """Evaluate user explanation using LLM rubric."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.pass_score = settings.LLM_EXPLANATION_PASS_SCORE
        self.timeout = settings.LLM_EXPLANATION_TIMEOUT_SECONDS
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def evaluate(
        self,
        problem_title: str,
        problem_description: str,
        constraints: List[str],
        hints: List[str],
        expected_outputs: List[Any],
        expected_schema: List[str],
        answer_payload: Dict[str, Any]
    ) -> ExplanationEvaluation:
        if not expected_schema:
            return ExplanationEvaluation(
                score=0,
                passed=False,
                feedback="채점 가능한 답안 스키마가 없습니다. 문제 설정을 확인해주세요.",
                breakdown={"accuracy": 0, "relevance": 0, "clarity": 0, "evidence": 0}
            )

        if not answer_payload:
            return ExplanationEvaluation(
                score=0,
                passed=False,
                feedback="답안이 비어 있습니다. 요구된 키에 맞춰 답안을 작성해주세요.",
                breakdown={"accuracy": 0, "relevance": 0, "clarity": 0, "evidence": 0}
            )

        if not self.client:
            return ExplanationEvaluation(
                score=0,
                passed=False,
                feedback="LLM 평가가 비활성화되어 있습니다. OPENAI_API_KEY를 설정해주세요.",
                breakdown={"accuracy": 0, "relevance": 0, "clarity": 0, "evidence": 0}
            )

        prompt = self._build_prompt(
            problem_title=problem_title,
            problem_description=problem_description,
            constraints=constraints,
            hints=hints,
            expected_outputs=expected_outputs,
            expected_schema=expected_schema,
            answer_payload=answer_payload
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prompt,
                response_format={"type": "json_object"},
                timeout=self.timeout
            )
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
        except Exception:
            return ExplanationEvaluation(
                score=0,
                passed=False,
                feedback="LLM 평가 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                breakdown={"accuracy": 0, "relevance": 0, "clarity": 0, "evidence": 0}
            )

        score = int(data.get("score", 0))
        score = max(0, min(100, score))
        breakdown = data.get("breakdown") or {}
        feedback = str(data.get("feedback", "")).strip()
        if not feedback:
            feedback = "설명에 대한 추가 피드백을 생성하지 못했습니다."

        return ExplanationEvaluation(
            score=score,
            passed=score >= self.pass_score,
            feedback=feedback,
            breakdown={
                "accuracy": int(breakdown.get("accuracy", 0)),
                "relevance": int(breakdown.get("relevance", 0)),
                "clarity": int(breakdown.get("clarity", 0)),
                "evidence": int(breakdown.get("evidence", 0))
            }
        )

    def _build_prompt(
        self,
        problem_title: str,
        problem_description: str,
        constraints: List[str],
        hints: List[str],
        expected_outputs: List[Any],
        expected_schema: List[str],
        answer_payload: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        rubric = {
            "accuracy": 50,
            "relevance": 20,
            "clarity": 20,
            "evidence": 10
        }
        expected_summary = self._summarize_expected_outputs(expected_outputs, expected_schema)
        return [
            {
                "role": "system",
                "content": (
                    "너는 코드 문제의 답안(dict)을 평가하는 엄격한 채점자다. "
                    "반드시 JSON만 반환하라. 한국어로 피드백을 작성하라. "
                    "답안에 포함된 내용만 평가하고, 힌트나 기대 출력으로 정답을 추론하지 마라. "
                    "답안이 비어 있거나 누락/모호하면 낮은 점수를 부여하라."
                )
            },
            {
                "role": "user",
                "content": (
                    "다음 답안을 루브릭에 따라 0~100점으로 평가해라.\n\n"
                    f"[문제 제목]\n{problem_title}\n\n"
                    f"[문제 설명]\n{problem_description}\n\n"
                    f"[제약]\n{constraints}\n\n"
                    f"[힌트]\n{hints}\n\n"
                    f"[기대 스키마]\n{expected_schema}\n\n"
                    f"[기대 출력(요약)]\n{expected_summary}\n\n"
                    f"[사용자 답안(JSON)]\n{json.dumps(answer_payload, ensure_ascii=False)}\n\n"
                    "[루브릭]\n"
                    f"- 정확성({rubric['accuracy']})\n"
                    f"- 관련성({rubric['relevance']})\n"
                    f"- 명확성({rubric['clarity']})\n"
                    f"- 근거/예시({rubric['evidence']})\n\n"
                    "반환 JSON 형식:\n"
                    "{\n"
                    '  "score": 0-100,\n'
                    '  "feedback": "한국어 피드백",\n'
                    '  "breakdown": {\n'
                    '    "accuracy": 0-50,\n'
                    '    "relevance": 0-20,\n'
                    '    "clarity": 0-20,\n'
                    '    "evidence": 0-10\n'
                    "  }\n"
                    "}\n"
                )
            }
        ]

    def _summarize_expected_outputs(
        self,
        expected_outputs: List[Any],
        expected_schema: List[str]
    ) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        for key in expected_schema:
            values = []
            for output in expected_outputs:
                if isinstance(output, dict) and key in output:
                    values.append(output.get(key))
            if not values:
                continue
            unique_values = list({json.dumps(v, sort_keys=True) for v in values})
            if len(unique_values) == 1:
                summary[key] = values[0]
            else:
                summary[key] = [json.loads(v) for v in unique_values]
        return summary
