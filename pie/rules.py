import logging

logger = logging.getLogger("wellmate_pie_rules")

def apply_clinical_rules(missions: list, twin_state: dict, active_mission_ids: list = None) -> list:
    """
    Applies clinical safety rules and context matching to filter out inappropriate missions.
    twin_state contains keys: stress, anxiety, fatigue, social, academic, sleep, mood, resilience, focus, etc.
    active_mission_ids is a list of mission_ids that are currently active for the student.
    """
    if active_mission_ids is None:
        active_mission_ids = []
        
    filtered = []
    fatigue = twin_state.get("fatigue", 0.5)
    sleep = twin_state.get("sleep", 0.7)
    screen_time = twin_state.get("screen_time", 0.5)
    
    for item in missions:
        m_id = item["mission_id"]
        category = item["category"]
        
        # Rule A: Do not suggest if the mission is already active
        if m_id in active_mission_ids:
            logger.info(f"Rule Filter: Excluded '{m_id}' because it is already active.")
            continue
            
        # Rule B: If fatigue is critical (>0.85), exclude heavy physical or intensive academic tasks
        if fatigue > 0.85 and category in ["physical", "academic"]:
            # Exclude intensive tasks, but keep light stretching or priority matrix
            if m_id not in ["physical-stretching-flow", "academic-matrix-priority"]:
                logger.info(f"Rule Filter: Excluded '{m_id}' due to critical fatigue level ({fatigue:.2f}).")
                continue
                
        # Rule C: If sleep is excellent (>0.85), skip sleep hygiene missions to focus on other areas
        if sleep > 0.85 and category == "sleep":
            logger.info(f"Rule Filter: Excluded sleep mission '{m_id}' since student sleep is excellent ({sleep:.2f}).")
            continue
            
        filtered.append(item)
        
    return filtered
