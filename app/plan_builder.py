import os
import json

# Paths to data files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES_PATH = os.path.join(BASE_DIR, "docs", "candidates.json")
CURRICULUM_PATH = os.path.join(BASE_DIR, "docs", "curriculum.json")

CORE_TOPIC_DAYS = [8, 9, 10, 11, 12, 13, 20, 21, 22, 23, 24, 28]

def load_data():
    """Load candidates and curriculum from JSON files."""
    if not os.path.exists(CANDIDATES_PATH):
        raise FileNotFoundError(f"Candidates file not found at {CANDIDATES_PATH}")
    if not os.path.exists(CURRICULUM_PATH):
        raise FileNotFoundError(f"Curriculum file not found at {CURRICULUM_PATH}")
        
    with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
        candidates_data = json.load(f)
    with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
        curriculum_data = json.load(f)
        
    return candidates_data, curriculum_data

def get_candidate_by_id(candidates_data, candidate_id):
    """Find a candidate by ID."""
    for cand in candidates_data.get("candidates", []):
        if cand.get("member", {}).get("id") == candidate_id:
            return cand
    return None

def get_curriculum_day(curriculum_data, day_num):
    """Find curriculum details for a specific day."""
    for day in curriculum_data.get("days", []):
        if day.get("day") == day_num:
            return day
    return None

def build_plan_for_candidate(candidate, curriculum_data):
    """
    Build a personalized plan for a candidate containing exactly 6 distinct days.
    - One "strength" (mission passed on first attempt)
    - One "struggle" (mission taking 3+ attempts)
    - One "gap" (mission failed or skipped)
    - Core completed topics to fill the remaining slots
    """
    missions = candidate.get("missions", [])
    
    # 1. Select Strength
    strength_mission = None
    # Priority 1: passed and attempts == 1
    strength_options = [m for m in missions if m.get("passed") is True and m.get("attempts") == 1]
    if strength_options:
        strength_mission = strength_options[0]
    else:
        # Priority 2: passed and attempts == 2
        strength_options = [m for m in missions if m.get("passed") is True and m.get("attempts") == 2]
        if strength_options:
            strength_mission = strength_options[0]
        else:
            # Priority 3: passed
            strength_options = [m for m in missions if m.get("passed") is True]
            if strength_options:
                strength_mission = strength_options[0]
                
    # 2. Select Struggle
    struggle_mission = None
    exclude_days = set()
    if strength_mission:
        exclude_days.add(strength_mission["day"])
        
    # Priority 1: attempts >= 3
    struggle_options = [m for m in missions if m["day"] not in exclude_days and m.get("attempts", 0) >= 3]
    if struggle_options:
        struggle_mission = struggle_options[0]
    else:
        # Priority 2: attempts == 2
        struggle_options = [m for m in missions if m["day"] not in exclude_days and m.get("attempts", 0) == 2]
        if struggle_options:
            struggle_mission = struggle_options[0]
        else:
            # Priority 3: any other mission
            struggle_options = [m for m in missions if m["day"] not in exclude_days]
            if struggle_options:
                struggle_mission = struggle_options[0]
                
    # 3. Select Gap
    gap_mission = None
    if struggle_mission:
        exclude_days.add(struggle_mission["day"])
        
    # Priority 1: passed is False or skipped is True
    gap_options = [m for m in missions if m["day"] not in exclude_days and (m.get("passed") is False or m.get("skipped") is True)]
    if gap_options:
        gap_mission = gap_options[0]
    else:
        # Priority 2: any other mission
        gap_options = [m for m in missions if m["day"] not in exclude_days]
        if gap_options:
            gap_mission = gap_options[0]
            
    if gap_mission:
        exclude_days.add(gap_mission["day"])
        
    # Construct plan items
    plan_items = []
    
    if strength_mission:
        day_info = get_curriculum_day(curriculum_data, strength_mission["day"])
        if day_info:
            plan_items.append({
                "day": strength_mission["day"],
                "title": day_info.get("title"),
                "type": "strength",
                "reason": f"Passed on attempt {strength_mission.get('attempts', 1)}, showing good confidence and mastery.",
                "tools": day_info.get("tools", []),
                "objectives": day_info.get("objectives", [])
            })
            
    if struggle_mission:
        day_info = get_curriculum_day(curriculum_data, struggle_mission["day"])
        if day_info:
            plan_items.append({
                "day": struggle_mission["day"],
                "title": day_info.get("title"),
                "type": "struggle",
                "reason": f"Took {struggle_mission.get('attempts', 3)} attempts to complete. Probing to verify if key concepts are fully understood.",
                "tools": day_info.get("tools", []),
                "objectives": day_info.get("objectives", [])
            })
            
    if gap_mission:
        day_info = get_curriculum_day(curriculum_data, gap_mission["day"])
        if day_info:
            status_str = "skipped" if gap_mission.get("skipped") else f"failed after {gap_mission.get('attempts', 0)} attempts"
            plan_items.append({
                "day": gap_mission["day"],
                "title": day_info.get("title"),
                "type": "gap",
                "reason": f"This mission was {status_str}. Testing foundational knowledge of the topic without assuming complete lock-out.",
                "tools": day_info.get("tools", []),
                "objectives": day_info.get("objectives", [])
            })
            
    # 4. Fill remaining slots with core completed topics to reach exactly 6 days
    selected_days = {item["day"] for item in plan_items}
    
    # Priority A: Core topics passed
    core_passed = [m for m in missions if m["day"] not in selected_days and m["day"] in CORE_TOPIC_DAYS and m.get("passed") is True]
    for m in core_passed:
        if len(plan_items) >= 6:
            break
        day_info = get_curriculum_day(curriculum_data, m["day"])
        if day_info:
            plan_items.append({
                "day": m["day"],
                "title": day_info.get("title"),
                "type": "core",
                "reason": f"Core completed topic on {day_info.get('title')}. Verifying alignment with objectives.",
                "tools": day_info.get("tools", []),
                "objectives": day_info.get("objectives", [])
            })
            selected_days.add(m["day"])
            
    # Priority B: Other completed topics passed
    other_passed = [m for m in missions if m["day"] not in selected_days and m.get("passed") is True]
    for m in other_passed:
        if len(plan_items) >= 6:
            break
        day_info = get_curriculum_day(curriculum_data, m["day"])
        if day_info:
            plan_items.append({
                "day": m["day"],
                "title": day_info.get("title"),
                "type": "core",
                "reason": f"Completed topic on {day_info.get('title')}. Assessing practical experience.",
                "tools": day_info.get("tools", []),
                "objectives": day_info.get("objectives", [])
            })
            selected_days.add(m["day"])
            
    # Priority C: Other attempted/skipped topics in candidate's list
    remaining_missions = [m for m in missions if m["day"] not in selected_days]
    for m in remaining_missions:
        if len(plan_items) >= 6:
            break
        day_info = get_curriculum_day(curriculum_data, m["day"])
        if day_info:
            plan_items.append({
                "day": m["day"],
                "title": day_info.get("title"),
                "type": "core",
                "reason": f"Assessing understanding of {day_info.get('title')}.",
                "tools": day_info.get("tools", []),
                "objectives": day_info.get("objectives", [])
            })
            selected_days.add(m["day"])
            
    # Priority D: Global curriculum fallback (if candidate has < 6 days in their record)
    if len(plan_items) < 6:
        for day_info in curriculum_data.get("days", []):
            if len(plan_items) >= 6:
                break
            day_num = day_info.get("day")
            if day_num not in selected_days:
                plan_items.append({
                    "day": day_num,
                    "title": day_info.get("title"),
                    "type": "core",
                    "reason": f"Exploring knowledge in {day_info.get('title')}.",
                    "tools": day_info.get("tools", []),
                    "objectives": day_info.get("objectives", [])
                })
                selected_days.add(day_num)
                
    # Ensure they are ordered by day number to make the plan systematic
    plan_items = sorted(plan_items, key=lambda x: x["day"])
    
    return plan_items
