def grade(email, action):
    """
    Hard task grading.

    Score breakdown:
    0.4 → correct category
    0.3 → correct priority
    0.3 → correct final action
    """

    score = 0.0

    if action.get("category") == email.get("label"):
        score += 0.4

    if action.get("priority") == email.get("priority"):
        score += 0.3

    if action.get("final_action") == email.get("action"):
        score += 0.3

    return score