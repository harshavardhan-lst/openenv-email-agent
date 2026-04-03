def grade(email, action):
    """
    Medium task: classify email priority.
    """

    if action == email["label"]:
        return 1.0

    return 0.0