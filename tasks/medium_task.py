from graders.grader_medium import grade


class MediumTask:
    """
    Medium task: Email priority classification.
    """

    def evaluate(self, email, action):
        return grade(email, action)