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
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None, db: Optional[AsyncIOMotorDatabase] = None):
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
        
        try:
            prompt = f"""You are an expert productivity coach specialized in SMART goal refinement.

PRODUCTIVITY GUIDELINES:
{self.PRODUCTIVITY_GUIDELINES}

USER'S GOAL: "{goal}"

TASK:
Analyze this goal and provide refined versions that better meet SMART criteria.
ALWAYS provide helpful refinements - never just reject the goal.

Evaluation criteria:
- Specific: Clearly defined outcome
- Measurable: Quantifiable or clear qualitative indicators
- Achievable: Realistic given constraints
- Relevant: Aligned with learning/productivity
- Time-bound: Has deadline or timeframe

Return ONLY valid JSON in this format:
{{
  "is_valid": true/false,
  "validation_details": {{
    "specific": true/false,
    "measurable": true/false,
    "achievable": true/false,
    "relevant": true/false,
    "time_bound": true/false
  }},
  "feedback": "Constructive analysis of the goal - what's good and what could be improved",
  "suggestions": [
    "Specific tip on how to make it more measurable",
    "How to add concrete milestones",
    "How to make the timeframe clearer"
  ],
  "refined_versions": [
    {{
      "goal": "First refined version of the goal",
      "improvement": "What makes this version better",
      "why_better": "Specific improvements made"
    }},
    {{
      "goal": "Second refined version (more ambitious)",
      "improvement": "What makes this version better",
      "why_better": "Specific improvements made"
    }},
    {{
      "goal": "Third refined version (most structured)",
      "improvement": "What makes this version better",
      "why_better": "Specific improvements made"
    }}
  ]
}}

Important: Always provide 3 refined versions even if the goal is already good. Show progressively better/more detailed versions."""

            content = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt="You are a helpful productivity coach. Refine and improve goals constructively. Always return valid JSON.",
                temperature=0.5,
                max_tokens=1500,
                json_mode=True
            )
            
            # Extract JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            result = json.loads(content)
            
            # Ensure refined_versions exists
            if 'refined_versions' not in result or not result['refined_versions']:
                result['refined_versions'] = [
                    {
                        "goal": goal,
                        "improvement": "Original goal",
                        "why_better": "Use this version if you prefer your original phrasing"
                    }
                ]
            
            logger.info(f"Goal analysis: '{goal}' -> {'VALID' if result['is_valid'] else 'NEEDS_REFINEMENT'} with {len(result['refined_versions'])} suggestions")
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating goal with LLM: {e}")
            return self._basic_goal_validation(goal)
    
    def _basic_goal_validation(self, goal: str) -> Dict[str, Any]:
        """Fallback validation without LLM"""
        # Basic checks
        is_specific = len(goal.split()) > 3
        has_measurable_indicators = bool(re.search(r'\d+|deadline|by|until|complete', goal, re.IGNORECASE))
        
        # Create basic refined versions
        refined_versions = [
            {
                "goal": goal,
                "improvement": "Original goal",
                "why_better": "Your original phrasing"
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
                "time_bound": has_measurable_indicators
            },
            "feedback": "Goal validated using basic criteria. LLM validation recommended for better accuracy.",
            "suggestions": [
                "Make the goal more specific with concrete outcomes" if not is_specific else "Good level of specificity",
                "Add measurable criteria (numbers, deadlines, concrete deliverables)" if not has_measurable_indicators else "Has measurable elements",
                "Consider including a timeframe (e.g., 'within 8 weeks', 'by March 1st')" if not has_measurable_indicators else "Well defined"
            ],
            "refined_versions": refined_versions,
            "improved_goal": None
        }
    
    async def suggest_tasks_for_goal(
        self,
        goal: str
    ) -> Dict[str, Any]:
        """
        Suggest tasks that would help achieve the goal, following productivity guidelines.
        
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
        
        try:
            prompt = f"""You are an expert productivity coach. Create a breakdown of tasks to achieve this goal.

PRODUCTIVITY GUIDELINES:
{self.PRODUCTIVITY_GUIDELINES}

USER'S GOAL: "{goal}"

IMPORTANT NOTES:
- Infer a reasonable timeframe from the goal (if not specified, assume 4-8 weeks)
- Assume moderate availability (15-25 hours/week) unless goal suggests otherwise
- Energy preferences will be learned from weekly feedback over time

TASK CREATION RULES:
1. Apply 80/20 rule - identify the 20% of tasks that will drive 80% of results
2. Batch similar tasks together (minimize cognitive switching cost)
3. Categorize tasks: research, coding, admin, networking
4. Assign energy levels: high (complex/creative), medium (moderate focus), low (routine)
5. Estimate realistic time (consider ultradian rhythm: 90-120 min focus blocks)
6. Prioritize based on Eisenhower Matrix (important vs urgent)
7. Consider task dependencies and optimal sequencing
8. Balance workload - don't overcommit (goal should stretch but not break)

TASK ARTIFACTS (choose ONE per task):
- research tasks → artifact: "notes"
- coding tasks → artifact: "code"
- admin tasks → artifact: "article" OR "notes"
- networking tasks → artifact: "notes"

IMPORTANT: Each field must contain exactly ONE value from its allowed options:
- category: Must be ONLY "research" OR "coding" OR "admin" OR "networking" (not multiple values)
- artifact: Must be ONLY "article" OR "notes" OR "code" (not multiple values)
- energy_level: Must be ONLY "high" OR "medium" OR "low" (not multiple values)

Return ONLY valid JSON:
{{
  "suggested_tasks": [
    {{
      "title": "Clear, actionable task title",
      "category": "research",
      "time_hours": 1.5,
      "goal": "Why this task matters for the main goal",
      "artifact": "article",
      "priority": 8,
      "energy_level": "high",
      "batch_group": "Group name for batching similar tasks",
      "dependencies": ["task_title_it_depends_on"]
    }},
    {{
      "title": "Another task",
      "category": "coding",
      "time_hours": 2.0,
      "goal": "Task purpose",
      "artifact": "code",
      "priority": 9,
      "energy_level": "medium",
      "batch_group": "Development",
      "dependencies": []
    }}
  ],
  "scheduling_strategy": "Brief explanation of optimal scheduling approach",
  "estimated_total_hours": 12.5,
  "energy_allocation": {{
    "high_energy_hours": 6.0,
    "medium_energy_hours": 4.0,
    "low_energy_hours": 2.5
  }},
  "batching_recommendations": "How to batch these tasks for minimal context switching",
  "weekly_breakdown": "Monday: 2-3 hours (Tasks A,B), Tuesday: 3 hours (Task C)..."
}}

Important:
- Total hours MUST be realistic (don't exceed available_hours_per_week)
- Include mix of high/medium/low energy tasks
- Group similar tasks for batching
- Consider dependencies"""

            content = await self.llm_provider.generate(
                prompt=prompt,
                system_prompt="You are an expert task planner following productivity science. Always return valid JSON.",
                temperature=0.5,
                max_tokens=1500,
                json_mode=True
            )
            
            # Extract JSON
            logger.info(f"LLM response length: {len(content)} chars")
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            # Try to find JSON object in content if not already clean
            if not content.strip().startswith('{'):
                obj_match = re.search(r'\{.*\}', content, re.DOTALL)
                if obj_match:
                    content = obj_match.group(0)
            
            result = json.loads(content)
            logger.info(f"Generated {len(result.get('suggested_tasks', []))} tasks for goal: '{goal}'")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.error(f"Content (first 500 chars): {content[:500] if 'content' in locals() else 'N/A'}")
            return {
                "error": "Failed to generate tasks - JSON parsing error",
                "suggested_tasks": []
            }
        except Exception as e:
            logger.error(f"Error generating task suggestions: {type(e).__name__}: {e}")
            return {
                "error": f"Failed to generate tasks: {str(e)}",
                "suggested_tasks": []
            }
    
    async def analyze_goal_alignment(self, goal: str, existing_goals: List[str]) -> Dict[str, Any]:
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
                prompt=prompt,
                temperature=0.3,
                max_tokens=600,
                json_mode=True
            )
            
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error analyzing goal alignment: {e}")
            return {"alignment_score": 0.5, "conflicts": [], "synergies": []}
    
    async def suggest_goal_improvements(self, rejected_goal: str, validation_result: Dict) -> Dict[str, Any]:
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
                prompt=prompt,
                temperature=0.6,
                max_tokens=1000,
                json_mode=True
            )
            
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating goal improvements: {e}")
            return {"improved_versions": [], "tips": []}
