#!/usr/bin/env python3
"""
Test script to verify JSON repair logic for truncated LLM responses
"""

import json
import re

# Simulated truncated JSON from LLM (similar to what we see in logs)
truncated_json = """{
  "suggested_tasks": [
    {
      "title": "Research MongoDB Certification Requirements",
      "category": "research",
      "time_hours": 1.0,
      "goal": "Understand the certification process and requirements",
      "artifact": "notes",
      "priority": 10,
      "energy_level": "high",
      "batch_group": "Understanding the Basics",
      "dependencies": []
    },
    {
      "title": "Complete MongoDB Certification Study Materials",
      "category": "research",
      "time_hours": 2.5,
      "goal": "Master core MongoDB concepts",
      "artifact": "notes",
      "priority": 9,
      "energy_level": "high",
      "batch_group": "Study Phase",
      "dependencies": ["Research MongoDB Certification Requirements"]
    },
    {
      "title": "Practice MongoDB Query Optimization",
      "category": "coding",
      "time_hours": """

content = truncated_json

print("Testing JSON repair logic...")
print(f"Content length: {len(content)} chars")
print("\nAttempting to parse...")

try:
    result = json.loads(content)
    print("✓ JSON parsed successfully!")
except json.JSONDecodeError as json_err:
    print(f"✗ JSON parse failed: {json_err}")
    print("\nAttempting repair...")

    tasks = []
    tasks_match = re.search(r'"suggested_tasks":\s*\[(.*)', content, re.DOTALL)

    if tasks_match:
        tasks_content = tasks_match.group(1)
        print(f"Found tasks array, content length: {len(tasks_content)} chars")

        # Extract complete task objects
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

                    if brace_depth == 0 and current_task.strip():
                        task_candidates.append(current_task.strip())
                        current_task = ""
                elif brace_depth > 0:
                    current_task += char
            else:
                current_task += char

        print(f"\nFound {len(task_candidates)} task candidates")

        for idx, candidate in enumerate(task_candidates):
            try:
                task_obj = json.loads(candidate)
                if all(k in task_obj for k in ["title", "category", "time_hours"]):
                    task_obj.setdefault("goal", "Task goal")
                    task_obj.setdefault("artifact", "notes")
                    task_obj.setdefault("priority", 5)
                    task_obj.setdefault("energy_level", "medium")
                    task_obj.setdefault("batch_group", "General")
                    task_obj.setdefault("dependencies", [])
                    tasks.append(task_obj)
                    print(f"✓ Recovered task {idx + 1}: {task_obj['title']}")
            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse candidate {idx + 1}: {e}")

        if tasks:
            print(f"\n✓ Successfully recovered {len(tasks)} tasks!")
            result = {
                "suggested_tasks": tasks,
                "scheduling_strategy": "Tasks generated successfully",
                "estimated_total_hours": sum(t.get("time_hours", 1.0) for t in tasks),
            }
            print("\nRecovered result:")
            print(json.dumps(result, indent=2))
        else:
            print("\n✗ Could not recover any tasks")
    else:
        print("✗ Could not find suggested_tasks array")
