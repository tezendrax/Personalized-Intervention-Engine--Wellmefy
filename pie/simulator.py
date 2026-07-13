import numpy as np
import random
import math
from sqlalchemy.orm import Session
from pie.taxonomy import MISSION_POOL
from pie.rules import apply_clinical_rules
from pie.bandit import get_context_vector, load_or_init_parameters, compute_linucb_score, update_bandit_matrices

def get_true_preference_theta(profile: str, category: str) -> np.ndarray:
    """
    Returns the hidden true preference vector theta_true (15 dimensions) for a profile and category.
    When multiplied by the context vector, it determines the probability of success.
    """
    # Initialize base weights
    theta = np.zeros(15)
    
    # 15 dimensions:
    # 0: stress, 1: anxiety, 2: fatigue, 3: sleep_debt, 4: resilience_deficit
    # 5: mood, 6: focus, 7: academic_stress, 8: social_isolation
    # 9: time_of_day, 10: is_weekend, 11: screen_time_index, 12: calendar_availability
    # 13: steps_ratio, 14: past_completion_rate
    
    if profile == "Stressed Academic":
        # Stressed academic wants mental relief (stress, anxiety triggers it) and academic help, but dislikes physical/sleep tasks
        if category == "mental":
            theta[0] = 2.5  # stress
            theta[1] = 2.0  # anxiety
            theta[14] = 1.0 # past completion
        elif category == "academic":
            theta[7] = 3.0  # academic stress makes them do academic tasks
            theta[6] = 1.5  # focus helps
            theta[12] = 1.0 # availability
        elif category == "physical":
            theta[2] = -2.5 # high fatigue makes them refuse physical tasks
        elif category == "sleep":
            theta[3] = -2.0 # high sleep debt makes them study instead of sleeping (academic stress overcomes sleep)
            
    elif profile == "Late-Night Gamer":
        # Gamer likes social and digital tasks, dislikes academic tasks
        if category == "digital":
            theta[11] = 3.0  # screen time index makes them receptive to digital balance
            theta[5] = -1.0  # low mood makes them seek detox
        elif category == "social":
            theta[8] = 2.0   # isolation makes them seek social contact
            theta[10] = 1.5  # weekends are great for social
        elif category == "academic":
            theta[7] = -3.0  # refuse academic work
            
    else: # Balanced Student
        # Balanced student is receptive to everything, especially physical/sleep/social
        theta[14] = 2.0      # high past completion rate
        if category == "physical":
            theta[13] = 1.5  # steps ratio
            theta[2] = 0.5   # light fatigue is fine
        elif category == "sleep":
            theta[3] = 2.0   # sleep debt triggers sleep tasks
        elif category == "social":
            theta[8] = 1.0   # handles isolation well
            
    return theta

def generate_simulated_context(profile: str) -> tuple:
    """
    Generates synthetic twin_state and user_context based on student profile.
    Adds random noise for realism.
    """
    twin_state = {}
    user_context = {}
    
    if profile == "Stressed Academic":
        twin_state["stress"] = clip(random.normalvariate(0.8, 0.1))
        twin_state["anxiety"] = clip(random.normalvariate(0.7, 0.1))
        twin_state["fatigue"] = clip(random.normalvariate(0.7, 0.1))
        twin_state["sleep"] = clip(random.normalvariate(0.4, 0.1))
        twin_state["resilience"] = clip(random.normalvariate(0.4, 0.1))
        twin_state["mood"] = clip(random.normalvariate(0.4, 0.1))
        twin_state["focus"] = clip(random.normalvariate(0.5, 0.1))
        twin_state["academic"] = clip(random.normalvariate(0.8, 0.1))
        twin_state["social"] = clip(random.normalvariate(0.3, 0.1))
        
        user_context["time_of_day"] = clip(random.normalvariate(0.7, 0.15))
        user_context["is_weekend"] = 1.0 if random.random() < 0.2 else 0.0
        user_context["screen_time_index"] = clip(random.normalvariate(0.6, 0.15))
        user_context["calendar_availability"] = clip(random.normalvariate(0.3, 0.1))
        user_context["steps_ratio"] = clip(random.normalvariate(0.4, 0.2))
        user_context["past_completion_rate"] = clip(random.normalvariate(0.5, 0.1))
        
    elif profile == "Late-Night Gamer":
        twin_state["stress"] = clip(random.normalvariate(0.5, 0.15))
        twin_state["anxiety"] = clip(random.normalvariate(0.5, 0.15))
        twin_state["fatigue"] = clip(random.normalvariate(0.8, 0.1))
        twin_state["sleep"] = clip(random.normalvariate(0.3, 0.1))
        twin_state["resilience"] = clip(random.normalvariate(0.6, 0.1))
        twin_state["mood"] = clip(random.normalvariate(0.5, 0.1))
        twin_state["focus"] = clip(random.normalvariate(0.4, 0.1))
        twin_state["academic"] = clip(random.normalvariate(0.4, 0.1))
        twin_state["social"] = clip(random.normalvariate(0.5, 0.15))
        
        user_context["time_of_day"] = clip(random.normalvariate(0.9, 0.1))
        user_context["is_weekend"] = 1.0 if random.random() < 0.4 else 0.0
        user_context["screen_time_index"] = clip(random.normalvariate(0.9, 0.05))
        user_context["calendar_availability"] = clip(random.normalvariate(0.7, 0.15))
        user_context["steps_ratio"] = clip(random.normalvariate(0.3, 0.1))
        user_context["past_completion_rate"] = clip(random.normalvariate(0.4, 0.1))
        
    else: # Balanced Student
        twin_state["stress"] = clip(random.normalvariate(0.3, 0.1))
        twin_state["anxiety"] = clip(random.normalvariate(0.2, 0.1))
        twin_state["fatigue"] = clip(random.normalvariate(0.3, 0.1))
        twin_state["sleep"] = clip(random.normalvariate(0.8, 0.1))
        twin_state["resilience"] = clip(random.normalvariate(0.8, 0.1))
        twin_state["mood"] = clip(random.normalvariate(0.7, 0.1))
        twin_state["focus"] = clip(random.normalvariate(0.8, 0.1))
        twin_state["academic"] = clip(random.normalvariate(0.3, 0.1))
        twin_state["social"] = clip(random.normalvariate(0.8, 0.1))
        
        user_context["time_of_day"] = clip(random.normalvariate(0.5, 0.2))
        user_context["is_weekend"] = 1.0 if random.random() < 0.28 else 0.0
        user_context["screen_time_index"] = clip(random.normalvariate(0.4, 0.1))
        user_context["calendar_availability"] = clip(random.normalvariate(0.6, 0.1))
        user_context["steps_ratio"] = clip(random.normalvariate(1.0, 0.15))
        user_context["past_completion_rate"] = clip(random.normalvariate(0.85, 0.05))
        
    return twin_state, user_context

def clip(val, min_v=0.0, max_v=1.0):
    return max(min_v, min(max_v, val))

def run_simulation(db: Session, profile_name: str, iterations: int = 100) -> dict:
    """
    Simulates a batch of recommendation requests and user choices to train LinUCB.
    Returns tracking logs showing convergence statistics.
    """
    rewards = []
    regrets = []
    history = []
    
    for i in range(iterations):
        # 1. Generate state
        twin_state, user_context = generate_simulated_context(profile_name)
        x_t = get_context_vector(twin_state, user_context)
        
        # 2. Filter via clinical rules
        filtered_missions = apply_clinical_rules(MISSION_POOL, twin_state)
        if not filtered_missions:
            filtered_missions = MISSION_POOL
            
        # 3. Compute LinUCB score & select best
        best_mission = None
        best_score = -float('inf')
        
        # We also compute the true optimal mission (the one with the highest true expectation)
        optimal_mission = None
        optimal_prob = -float('inf')
        
        for m in filtered_missions:
            m_id = m["mission_id"]
            cat = m["category"]
            
            # LinUCB score
            A, b, _ = load_or_init_parameters(db, m_id)
            score = compute_linucb_score(A, b, x_t)
            
            if score > best_score:
                best_score = score
                best_mission = m
                
            # True expectation for regret calculation
            theta_true = get_true_preference_theta(profile_name, cat)
            true_prob = 1.0 / (1.0 + math.exp(-clip(np.dot(x_t, theta_true), -10.0, 10.0)))
            if true_prob > optimal_prob:
                optimal_prob = true_prob
                optimal_mission = m
                
        # 4. Simulate user choice (Bernoulli trial based on true preference of chosen mission)
        chosen_cat = best_mission["category"]
        theta_true_chosen = get_true_preference_theta(profile_name, chosen_cat)
        success_prob = 1.0 / (1.0 + math.exp(-clip(np.dot(x_t, theta_true_chosen), -10.0, 10.0)))
        
        reward = 1.0 if random.random() < success_prob else 0.0
        rewards.append(reward)
        
        # Regret = Optimal Prob - Chosen Prob
        regret = max(0.0, optimal_prob - success_prob)
        regrets.append(regret)
        
        # 5. Update bandit Matrices
        update_bandit_matrices(db, best_mission["mission_id"], x_t, reward)
        
        if (i + 1) % 10 == 0 or i == 0 or i == iterations - 1:
            history.append({
                "iteration": i + 1,
                "chosen_mission": best_mission["mission_id"],
                "chosen_category": chosen_cat,
                "reward": reward,
                "success_probability": float(success_prob),
                "regret": float(regret),
                "running_ctr": float(np.mean(rewards)),
                "running_regret": float(np.mean(regrets))
            })
            
    return {
        "profile_name": profile_name,
        "total_iterations": iterations,
        "final_ctr": float(np.mean(rewards)),
        "final_regret": float(np.mean(regrets)),
        "history": history
    }
