from graders.grader_hard import grade


class HardTask:
    """
    Hard task: Full inbox management.
    """

    def evaluate(self, email, action):
        return grade(email, action)