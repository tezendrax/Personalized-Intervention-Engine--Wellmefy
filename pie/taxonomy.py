# Catalog of student recovery missions mapping specific wellness, academic, and lifestyle issues

MISSION_POOL = [
    {
        "mission_id": "academic-pomodoro-focus",
        "category": "academic",
        "title": "25-Minute Pomodoro Focus",
        "description": "Engage in 25 minutes of completely focused study on your highest priority backlog task, followed by a 5-minute offline break.",
        "difficulty": 0.5,
        "points_value": 50,
        "rationale_template": "Recommended to break academic procrastination and chip away at assignment backlogs."
    },
    {
        "mission_id": "academic-backlog-builder",
        "category": "academic",
        "title": "Academic Backlog Audit",
        "description": "List all your pending assignments, exam topics, and projects with estimated hours needed for completion. Break them into micro-steps.",
        "difficulty": 0.6,
        "points_value": 60,
        "rationale_template": "Recommended because academic stress indicators are high and structuring backlogs reduces anxiety."
    },
    {
        "mission_id": "academic-matrix-priority",
        "category": "academic",
        "title": "Task Prioritization Matrix",
        "description": "Draw a 2x2 Eisenhower matrix (Urgent vs. Important) to categorize tasks. Commit to completing only the 'Urgent & Important' items first.",
        "difficulty": 0.4,
        "points_value": 40,
        "rationale_template": "Recommended to combat high cognitive load by deprioritizing non-essential tasks."
    },
    {
        "mission_id": "academic-study-spot",
        "category": "academic",
        "title": "Study Environment Swap",
        "description": "Move your study setup to a quiet, distraction-free environment like a library silent zone or a dedicated study room.",
        "difficulty": 0.3,
        "points_value": 30,
        "rationale_template": "Recommended to improve concentration and focus when academic environment feels cluttered."
    },
    {
        "mission_id": "mental-breathing-box",
        "category": "mental",
        "title": "5-Minute Box Breathing",
        "description": "Inhale for 4 seconds, hold for 4 seconds, exhale for 4 seconds, hold for 4 seconds. Repeat this box cycle for 5 minutes.",
        "difficulty": 0.2,
        "points_value": 30,
        "rationale_template": "Recommended to immediately lower acute somatic stress and restore heart rate variability."
    },
    {
        "mission_id": "mental-grounding-54321",
        "category": "mental",
        "title": "5-4-3-2-1 Sensory Grounding",
        "description": "Identify 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste to anchor yourself in the present.",
        "difficulty": 0.3,
        "points_value": 40,
        "rationale_template": "Recommended to disrupt negative anxiety feedback loops and racing thoughts."
    },
    {
        "mission_id": "mental-gratitude-list",
        "category": "mental",
        "title": "Three-Point Gratitude Log",
        "description": "Write down 3 specific, small things you are grateful for today (e.g., a good cup of coffee, a kind text) and why.",
        "difficulty": 0.2,
        "points_value": 30,
        "rationale_template": "Recommended to shift focus away from academic pressures and improve baseline mood."
    },
    {
        "mission_id": "mental-positive-journal",
        "category": "mental",
        "title": "Cognitive Reappraisal Journal",
        "description": "Write down a stressful event or thought. Write a reframing analysis from a neutral or positive perspective.",
        "difficulty": 0.5,
        "points_value": 50,
        "rationale_template": "Recommended to bolster psychological resilience and counter negative self-talk."
    },
    {
        "mission_id": "body-stretching-flow",
        "category": "physical",
        "title": "10-Minute Desk Stretching",
        "description": "Perform neck rolls, shoulder rolls, wrist stretches, and hamstring stretches to release physical tension built up from long desk sessions.",
        "difficulty": 0.3,
        "points_value": 40,
        "rationale_template": "Recommended to address physical fatigue, muscle stiffness, and somatic complaints."
    },
    {
        "mission_id": "body-planning-walk",
        "category": "physical",
        "title": "15-Minute Planning Walk",
        "description": "Take a 15-minute walk outside. Do not look at your phone. Use this time to mentally plan your day or simply observe your surroundings.",
        "difficulty": 0.4,
        "points_value": 50,
        "rationale_template": "Recommended to boost physical activity and lower high cortisol levels."
    },
    {
        "mission_id": "body-cardio-burst",
        "category": "physical",
        "title": "5-Minute Cortisol Release",
        "description": "Engage in 5 minutes of light, active movement (jumping jacks, high knees, or brisk climbing) to metabolize stress hormones.",
        "difficulty": 0.4,
        "points_value": 45,
        "rationale_template": "Recommended to discharge physical energy and alleviate feelings of high anxiety."
    },
    {
        "mission_id": "body-sun-exposure",
        "category": "physical",
        "title": "Outdoor Sunlight Reset",
        "description": "Spend 10-15 minutes outside in the direct daylight to help regulate your circadian rhythm and boost Vitamin D.",
        "difficulty": 0.2,
        "points_value": 30,
        "rationale_template": "Recommended to combat fatigue, improve mood, and anchor circadian sleep signals."
    },
    {
        "mission_id": "sleep-digital-detox",
        "category": "sleep",
        "title": "Pre-Sleep Digital Detox",
        "description": "Power down all phone, laptop, and tablet screens 45 minutes before your target bedtime to avoid blue light exposure.",
        "difficulty": 0.6,
        "points_value": 70,
        "rationale_template": "Recommended to reduce sleep debt and promote natural melatonin secretion."
    },
    {
        "mission_id": "sleep-wind-down",
        "category": "sleep",
        "title": "20-Minute Wind-Down Ritual",
        "description": "Read a physical book, listen to a calming podcast/music, or write in a journal for 20 minutes before sleeping. Keep the room dimly lit.",
        "difficulty": 0.4,
        "points_value": 50,
        "rationale_template": "Recommended to quiet the central nervous system before attempting sleep."
    },
    {
        "mission_id": "sleep-caffeine-cutoff",
        "category": "sleep",
        "title": "Caffeine Curfew",
        "description": "Commit to avoiding all caffeinated beverages (coffee, energy drinks, black tea) after 2:00 PM today.",
        "difficulty": 0.5,
        "points_value": 55,
        "rationale_template": "Recommended because caffeine intake late in the day disrupts deep sleep cycles."
    },
    {
        "mission_id": "sleep-bedtime-anchor",
        "category": "sleep",
        "title": "Bedtime Consistency Anchor",
        "description": "Go to bed within 30 minutes of your target bedtime tonight. Avoid looking at notifications once in bed.",
        "difficulty": 0.5,
        "points_value": 60,
        "rationale_template": "Recommended to stabilize your sleep pattern and reduce chronic sleep debt."
    },
    {
        "mission_id": "social-chat-friend",
        "category": "social",
        "title": "Connect with a Friend",
        "description": "Call, video chat, or meet a close friend for 10-15 minutes. Share how your week is going, and listen to theirs.",
        "difficulty": 0.3,
        "points_value": 40,
        "rationale_template": "Recommended to counter social isolation and improve emotional mood."
    },
    {
        "mission_id": "social-thank-you",
        "category": "social",
        "title": "Express Peer Appreciation",
        "description": "Send a short message or email of gratitude to a classmate, teacher, or friend who made a positive difference for you recently.",
        "difficulty": 0.3,
        "points_value": 45,
        "rationale_template": "Recommended to build positive social networks and boost sense of belonging."
    },
    {
        "mission_id": "social-coffee-peer",
        "category": "social",
        "title": "Classmate Coffee Break",
        "description": "Meet up with a classmate or study partner for a 15-minute tea/coffee break to chat about non-academic interests.",
        "difficulty": 0.4,
        "points_value": 50,
        "rationale_template": "Recommended to break study isolation and reduce burnout risk."
    },
    {
        "mission_id": "social-family-connect",
        "category": "social",
        "title": "Family Check-in",
        "description": "Call or message a family member or mentor for a quick personal catch-up.",
        "difficulty": 0.3,
        "points_value": 40,
        "rationale_template": "Recommended to reinforce your long-term emotional support network."
    },
    {
        "mission_id": "digital-grayscale-screen",
        "category": "digital",
        "title": "Grayscale Dopamine Detox",
        "description": "Switch your phone's display settings to grayscale. Keep it in grayscale for 24 hours to reduce impulsive screen checks.",
        "difficulty": 0.4,
        "points_value": 50,
        "rationale_template": "Recommended because excessive screen-time and smartphone usage are draining focus."
    },
    {
        "mission_id": "digital-phone-free-meal",
        "category": "digital",
        "title": "Phone-Free Dining",
        "description": "Eat lunch or dinner completely without your phone, laptop, or book nearby. Practice mindful eating.",
        "difficulty": 0.5,
        "points_value": 60,
        "rationale_template": "Recommended to disconnect from constant digital stimuli and lower stress."
    },
    {
        "mission_id": "digital-app-blocker",
        "category": "digital",
        "title": "Social App Timer Setup",
        "description": "Set a screen time limit (e.g., 30 minutes/day) for your most distracting social media application using native system settings.",
        "difficulty": 0.5,
        "points_value": 55,
        "rationale_template": "Recommended to reclaim time lost to doomscrolling and improve focus scores."
    },
    {
        "mission_id": "digital-notification-mute",
        "category": "digital",
        "title": "Notification Silence Block",
        "description": "Turn on 'Do Not Disturb' or place your phone in another room for a continuous 2-hour work session.",
        "difficulty": 0.3,
        "points_value": 40,
        "rationale_template": "Recommended to reduce context switching and improve deep work focus."
    }
]

def get_mission_by_id(mission_id: str) -> dict:
    return next((m for m in MISSION_POOL if m["mission_id"] == mission_id), None)
