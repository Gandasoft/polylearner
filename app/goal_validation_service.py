"""
Goal Validation Service
-----------------------
Service responsible for validating user goals using LLM and productivity guidelines.
Based on proven productivity principles including SMART goals, proactive mindset,
and energy management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import re

from llm_provider import LLMProvider
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class GoalValidationService:
    """
    Service for validating goals and suggesting tasks based on productivity guidelines.

    Core Principles (from LLM Guidelines):
    1. Proactive mindset - Goals should reflect ownership and intentionality
    2. Clear intentions - Goals must be specific and measurable
    3. SMART goals - Specific, Measurable, Achievable, Relevant, Time-bound
    4. Alignment - Goals should align with long-term vision
    5. Energy management - Consider natural rhythms and capacity
    """

    PRODUCTIVITY_GUIDELINES = """
Core Productivity Principles:

1. PROACTIVE MINDSET:
   - View challenges as opportunities
   - Take ownership of time and choices
   - Create conditions rather than wait for them

2. CLEAR INTENTIONS:
   - Define WHAT you want to achieve and WHY it matters
   - Goals should be crystal-clear, not vague
   - Must be measurable to track progress

3. SMART GOALS Framework:
   - Specific: Clearly defined, not ambiguous
   - Measurable: Quantifiable metrics or clear qualitative indicators
   - Achievable: Realistic given constraints
   - Relevant: Aligned with bigger picture
   - Time-bound: Has deadline or timeframe

4. PRIORITIZATION (Eisenhower Matrix):
   - Important tasks: Significant to achieving goals
   - Urgent tasks: Demand immediate attention
   - Focus on important over urgent
   - 80/20 rule: 20% of tasks drive 80% of results

5. ENERGY MANAGEMENT:
   - Circadian rhythm: 24-hour cycle of alertness
   - Ultradian rhythm: 90-120 min high focus, 20-30 min rest
   - High-energy periods for complex/creative work
   - Low-energy periods for routine/administrative tasks
   - Mandatory rest: 12am-6am (6 hours)

6. TASK BATCHING:
   - Group similar tasks to minimize cognitive switching cost
   - Batch by mental effort required
   - Batch by type (email, calls, creative work)

7. TIME BLOCKING:
   - Allocate specific time slots to tasks
   - Map non-negotiable commitments first
   - Leave buffer time for unforeseen events
   - Balance work, rest, and personal activities
"""

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        db: Optional[AsyncIOMotorDatabase] = None,
    ):
        self.llm_provider = llm_provider
        self.db = db

    async def validate_goal(self, goal: str) -> Dict[str, Any]:
        """
        Analyze and refine a goal using SMART criteria and productivity guidelines.
        Always provides refinement suggestions - never outright rejects.

        Returns:
            {
                "is_valid": bool,
                "validation_details": {
                    "specific": bool,
                    "measurable": bool,
                    "achievable": bool,
                    "relevant": bool,
                    "time_bound": bool
                },
                "feedback": str,
                "suggestions": List[str],
                "refined_versions": List[Dict] - Always provides 3 refined versions
            }
        """
        if not self.llm_provider or not self.llm_provider.is_available():
            logger.warning("LLM provider not available for goal validation")
            return self._basic_goal_validation(goal)

        # Get current date for context
        current_date = datetime.now()
        current_date_str = current_date.strftime("%B %d, %Y")

        try:
            prompt = f"""You are an expert productivity coach. Analyze this goal using SMART criteria.

CURRENT DATE: {current_date_str}
⚠️ All dates must be AFTER {current_date_str}

USER'S GOAL: "{goal}"

SMART EVALUATION:
- Specific: Clear, concrete outcome?
- Measurable: Quantifiable metrics or checkpoints?
- Achievable: Realistic for timeframe?
- Relevant: Aligned with growth/development?
- Time-bound: Has deadline after {current_date_str}?

REFINEMENT STRATEGY:
Provide 3 progressively refined versions of the user's goal:
- Version 1: Keep user's wording, add missing SMART elements
- Version 2: Restructure for clarity and measurability
- Version 3: Professional format with milestones and metrics

EXAMPLE (if goal was "learn Spanish"):
{{
  "refined_versions": [
    {{
      "goal": "Learn Spanish conversational skills to B1 level within 8 weeks",
      "improvement": "Added specific level (B1) and timeframe (8 weeks)",
      "why_better": "Makes success measurable and time-bound"
    }},
    {{
      "goal": "Achieve B1 Spanish fluency by completing 50 conversation sessions and scoring 80%+ on B1 practice test within 8 weeks",
      "improvement": "Added concrete metrics (50 sessions, 80% score)",
      "why_better": "Clear milestones to track progress"
    }},
    {{
      "goal": "Reach CEFR B1 Spanish proficiency by March 1, 2026 through: 50 conversation sessions (30min each), daily grammar practice (20min), and achieving 80%+ on official B1 practice exam",
      "improvement": "Specific date, detailed action plan, clear success criteria",
      "why_better": "Comprehensive plan with measurable checkpoints"
    }}
  ]
}}

YOUR TASK - Return ONLY valid JSON with ACTUAL refined goal statements (not placeholders):
{{
  "is_valid": true,
  "validation_details": {{
    "specific": true,
    "measurable": true,
    "achievable": true,
    "relevant": true,
    "time_bound": true
  }},
  "feedback": "Professional analysis of what's strong and what needs improvement",
  "suggestions": [
    "Specific actionable suggestion 1",
    "Specific actionable suggestion 2",
    "Specific actionable suggestion 3"
  ],
  "refined_versions": [
    {{
      "goal": "ACTUAL REFINED GOAL STATEMENT #1 - not a description",
      "improvement": "What was added/changed",
      "why_better": "Why this improves the goal"
    }},
    {{
      "goal": "ACTUAL REFINED GOAL STATEMENT #2 - more detailed than #1",
      "improvement": "What was enhanced",
      "why_better": "Benefits of these enhancements"
    }},
    {{
      "goal": "ACTUAL REFINED GOAL STATEMENT #3 - professional standard",
      "improvement": "Professional improvements made",
      "why_better": "Why this is the best version"
    }}
  ]
}}

QUALITY CHECKLIST:
☑ All timeframes are AFTER {current_date_str} (no past dates)
☑ Feedback is professional and constructive
☑ Each refined version is progressively better
☑ Suggestions are specific and actionable
☑ All SMART criteria are honestly evaluated"""

            content = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt=f"You are a professional productivity coach. Today is {current_date_str}. Never suggest past dates. IMPORTANT: In 'refined_versions', the 'goal' field must contain the ACTUAL refined goal statement, NOT a description or placeholder. Be precise, constructive, and professional. Always return valid JSON.",
                temperature=0.3,
                max_tokens=1000,
                json_mode=True,
            )

            # Extract JSON
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL
            )
            if json_match:
                content = json_match.group(1)

            result = json.loads(content)

            # Ensure refined_versions has at least 3 versions
            if "refined_versions" not in result or not result["refined_versions"]:
                result["refined_versions"] = []

            # Fill in missing versions to ensure we always have 3
            while len(result["refined_versions"]) < 3:
                version_num = len(result["refined_versions"]) + 1
                if version_num == 1:
                    result["refined_versions"].append(
                        {
                            "goal": goal,
                            "improvement": "Your original goal",
                            "why_better": "Start with your original phrasing and refine as you progress",
                        }
                    )
                elif version_num == 2:
                    result["refined_versions"].append(
                        {
                            "goal": f"{goal} with clear milestones and measurable outcomes",
                            "improvement": "Added structure and measurability",
                            "why_better": "Makes progress tracking easier and success criteria clearer",
                        }
                    )
                else:
                    result["refined_versions"].append(
                        {
                            "goal": f"{goal} - completed within 8 weeks with weekly checkpoints",
                            "improvement": "Added timeframe and accountability",
                            "why_better": "Creates urgency and allows for regular progress reviews",
                        }
                    )

            logger.info(
                f"Goal analysis: '{goal}' -> {'VALID' if result['is_valid'] else 'NEEDS_REFINEMENT'} with {len(result['refined_versions'])} suggestions"
            )

            return result

        except Exception as e:
            logger.error(f"Error validating goal with LLM: {e}")
            return self._basic_goal_validation(goal)

    def _basic_goal_validation(self, goal: str) -> Dict[str, Any]:
        """Fallback validation without LLM"""
        # Basic checks
        is_specific = len(goal.split()) > 3
        has_measurable_indicators = bool(
            re.search(r"\d+|deadline|by|until|complete", goal, re.IGNORECASE)
        )

        # Create basic refined versions
        refined_versions = [
            {
                "goal": goal,
                "improvement": "Original goal",
                "why_better": "Your original phrasing",
            }
        ]

        is_valid = is_specific and has_measurable_indicators

        return {
            "is_valid": is_valid,
            "validation_details": {
                "specific": is_specific,
                "measurable": has_measurable_indicators,
                "achievable": True,
                "relevant": True,
                "time_bound": has_measurable_indicators,
            },
            "feedback": "Goal validated using basic criteria. LLM validation recommended for better accuracy.",
            "suggestions": [
                "Make the goal more specific with concrete outcomes"
                if not is_specific
                else "Good level of specificity",
                "Add measurable criteria (numbers, deadlines, concrete deliverables)"
                if not has_measurable_indicators
                else "Has measurable elements",
                "Consider including a timeframe (e.g., 'within 8 weeks', 'by March 1st')"
                if not has_measurable_indicators
                else "Well defined",
            ],
            "refined_versions": refined_versions,
            "improved_goal": None,
        }

    async def suggest_tasks_for_goal(self, goal: str) -> Dict[str, Any]:
        """
        Suggest tasks that help achieve the goal, following productivity guidelines.

        Args:
            goal: The validated goal

        Note: Timeframe, available hours, and energy preferences are inferred from the goal
        and will be refined through weekly feedback analysis.

        Returns:
            {
                "suggested_tasks": List[Dict],
                "scheduling_strategy": str,
                "estimated_total_hours": float,
                "energy_allocation": Dict
            }
        """
        if not self.llm_provider or not self.llm_provider.is_available():
            logger.warning("LLM provider not available for task suggestions")
            return {"error": "LLM not available", "suggested_tasks": []}

        # Get current date for context
        current_date = datetime.now()
        current_date_str = current_date.strftime(
            "%B %d, %Y"
        )  # e.g., "January 15, 2026"

        try:
            prompt = f"""Create a task breakdown for this goal. Return ONLY valid JSON.

CURRENT DATE: {current_date_str}
GOAL: "{goal}"

Generate 6-10 tasks following these rules:
- Apply 80/20 rule (high-impact tasks first)
- Logical sequence (prerequisites first)
- Mix energy levels (high/medium/low)
- Realistic: 1-4h per task, 15-20h total

CONSTRAINTS:
- category: "research" | "coding" | "admin" | "networking"
- artifact: "notes" | "code" | "article"
- energy_level: "high" | "medium" | "low"
- priority: 1-10 (integer)
- time_hours: 0.5-4.0 (float)

JSON FORMAT (return exactly this structure):
{{
  "suggested_tasks": [
    {{
      "title": "Action-oriented task title",
      "category": "research",
      "time_hours": 2.0,
      "goal": "Brief purpose",
      "artifact": "notes",
      "priority": 9,
      "energy_level": "high",
      "batch_group": "Group name",
      "dependencies": []
    }}
  ],
  "scheduling_strategy": "Brief scheduling advice",
  "estimated_total_hours": 18.0,
  "energy_allocation": {{
    "high_energy_hours": 8.0,
    "medium_energy_hours": 7.0,
    "low_energy_hours": 3.0
  }},
  "batching_recommendations": "Brief batching advice",
  "weekly_breakdown": "Week-by-week summary"
}}"""

            content = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt=f"You are an expert task planner with deep domain knowledge across subjects. Today is {current_date_str}. NEVER suggest past dates. Be precise with timeframes and subject-specific methodology. Always return valid JSON.",
                temperature=0.3,
                max_tokens=2500,  # Increased to handle larger task lists
                json_mode=True,
            )

            # Extract JSON
            logger.info(f"LLM response length: {len(content)} chars")
            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL
            )
            if json_match:
                content = json_match.group(1)

            # Try to find JSON object in content if not already clean
            if not content.strip().startswith("{"):
                obj_match = re.search(r"\{.*\}", content, re.DOTALL)
                if obj_match:
                    content = obj_match.group(0)

            # Try to parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError as json_err:
                # If JSON is truncated, try to repair by extracting complete tasks
                logger.warning(f"JSON parse failed: {json_err}. Attempting repair...")
                logger.info(f"Full content length: {len(content)} chars")

                # Try to extract the array of tasks even if the overall JSON is broken
                tasks = []

                # Find the suggested_tasks array
                tasks_match = re.search(
                    r'"suggested_tasks":\s*\[(.*)', content, re.DOTALL
                )
                if tasks_match:
                    tasks_content = tasks_match.group(1)

                    # Split by task boundaries and try to parse each
                    # Look for complete task objects (matching braces)
                    task_candidates = []
                    brace_depth = 0
                    current_task = ""
                    in_string = False
                    escape_next = False

                    for i, char in enumerate(tasks_content):
                        if escape_next:
                            escape_next = False
                            current_task += char
                            continue

                        if char == "\\":
                            escape_next = True
                            current_task += char
                            continue

                        if char == '"' and not escape_next:
                            in_string = not in_string

                        if not in_string:
                            if char == "{":
                                if brace_depth == 0:
                                    current_task = "{"
                                else:
                                    current_task += char
                                brace_depth += 1
                            elif char == "}":
                                brace_depth -= 1
                                current_task += char

                                # Complete task object found
                                if brace_depth == 0 and current_task.strip():
                                    task_candidates.append(current_task.strip())
                                    current_task = ""
                            elif brace_depth > 0:
                                current_task += char
                        else:
                            current_task += char

                    # Try to parse each candidate
                    for candidate in task_candidates:
                        try:
                            task_obj = json.loads(candidate)
                            # Validate it has required fields
                            if all(
                                k in task_obj
                                for k in ["title", "category", "time_hours"]
                            ):
                                # Ensure all required fields exist with defaults
                                task_obj.setdefault("goal", "Task goal")
                                task_obj.setdefault("artifact", "notes")
                                task_obj.setdefault("priority", 5)
                                task_obj.setdefault("energy_level", "medium")
                                task_obj.setdefault("batch_group", "General")
                                task_obj.setdefault("dependencies", [])
                                tasks.append(task_obj)
                        except json.JSONDecodeError:
                            continue

                if tasks:
                    logger.info(
                        f"Recovered {len(tasks)} complete tasks from malformed JSON"
                    )
                    result = {
                        "suggested_tasks": tasks,
                        "scheduling_strategy": "Tasks generated successfully. Review and adjust as needed.",
                        "estimated_total_hours": sum(
                            t.get("time_hours", 1.0) for t in tasks
                        ),
                        "energy_allocation": {
                            "high_energy_hours": sum(
                                t.get("time_hours", 1.0)
                                for t in tasks
                                if t.get("energy_level") == "high"
                            ),
                            "medium_energy_hours": sum(
                                t.get("time_hours", 1.0)
                                for t in tasks
                                if t.get("energy_level") == "medium"
                            ),
                            "low_energy_hours": sum(
                                t.get("time_hours", 1.0)
                                for t in tasks
                                if t.get("energy_level") == "low"
                            ),
                        },
                        "batching_recommendations": "Group similar tasks to minimize context switching",
                        "weekly_breakdown": f"Total {len(tasks)} tasks over available weeks",
                    }
                else:
                    # If we can't recover any tasks, log full content and re-raise
                    logger.error(
                        f"Could not recover any tasks. Full content: {content}"
                    )
                    raise json_err

            logger.info(
                f"Generated {len(result.get('suggested_tasks', []))} tasks for goal: '{goal}'"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(
                f"Content (first 500 chars): {content[:500] if 'content' in locals() else 'N/A'}"
            )
            return {
                "error": "Failed to generate tasks - JSON parsing error",
                "suggested_tasks": [],
            }
        except Exception as e:
            logger.error(f"Error generating task suggestions: {type(e).__name__}: {e}")
            return {
                "error": f"Failed to generate tasks: {str(e)}",
                "suggested_tasks": [],
            }

    async def analyze_goal_alignment(
        self, goal: str, existing_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze if the new goal aligns with existing goals (avoiding conflicts).
        Checks for goal coherence and potential conflicts.
        """
        if not self.llm_provider or not self.llm_provider.is_available():
            return {"alignment_score": 0.5, "conflicts": [], "synergies": []}

        try:
            prompt = f"""Analyze if this new goal aligns with existing goals.

NEW GOAL: "{goal}"

EXISTING GOALS:
{chr(10).join(f"- {g}" for g in existing_goals) if existing_goals else "None"}

ANALYSIS CRITERIA:
1. Does the new goal conflict with existing goals (competing priorities, time conflicts)?
2. Does it synergize with existing goals (complementary skills, shared resources)?
3. Does it overcommit the user (too many goals at once)?
4. Is it coherent with the user's apparent focus areas?

Return ONLY valid JSON:
{{
  "alignment_score": 0.85,
  "conflicts": ["List of potential conflicts with existing goals"],
  "synergies": ["List of synergies and complementary aspects"],
  "recommendation": "approve|reject|defer",
  "reasoning": "Clear explanation of the recommendation"
}}"""

            content = await self.llm_provider.generate(
                prompt=prompt, temperature=0.3, max_tokens=600, json_mode=True
            )

            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL
            )
            if json_match:
                content = json_match.group(1)

            return json.loads(content)

        except Exception as e:
            logger.error(f"Error analyzing goal alignment: {e}")
            return {"alignment_score": 0.5, "conflicts": [], "synergies": []}

    async def suggest_goal_improvements(
        self, rejected_goal: str, validation_result: Dict
    ) -> Dict[str, Any]:
        """
        Provide detailed suggestions for improving a rejected goal.
        """
        if not self.llm_provider or not self.llm_provider.is_available():
            return {"improved_versions": [], "tips": []}

        try:
            prompt = f"""Help improve this rejected goal.

REJECTED GOAL: "{rejected_goal}"

VALIDATION ISSUES:
{json.dumps(validation_result, indent=2)}

GUIDELINES:
{self.PRODUCTIVITY_GUIDELINES}

Provide 3 improved versions of this goal that meet SMART criteria.

Return ONLY valid JSON:
{{
  "improved_versions": [
    {{
      "goal": "Improved goal statement",
      "why_better": "Explanation of improvements",
      "example_tasks": ["Task 1", "Task 2"]
    }}
  ],
  "key_tips": [
    "Specific tip for making goals measurable",
    "Tip for adding specificity"
  ]
}}"""

            content = await self.llm_provider.generate(
                prompt=prompt, temperature=0.6, max_tokens=1000, json_mode=True
            )

            json_match = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL
            )
            if json_match:
                content = json_match.group(1)

            return json.loads(content)

        except Exception as e:
            logger.error(f"Error generating goal improvements: {e}")
            return {"improved_versions": [], "tips": []}
