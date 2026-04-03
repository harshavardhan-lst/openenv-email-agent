def grade(email, action):
    
    label = email.get("label")

    correct_action_map = {
        "important": "mark_important",
        "archive": "archive_email",
        "delete": "delete_email"
    }

    correct_action = correct_action_map.get(label)

    if action == correct_action:
        return 1.0

    return -0.5