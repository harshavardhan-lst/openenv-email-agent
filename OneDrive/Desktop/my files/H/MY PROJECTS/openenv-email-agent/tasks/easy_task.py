from graders.grader_easy import grade

class EasyTask:
    """
    Easy task: Spam detection.
    The agent must classify whether an email is spam.
    """

    def evaluate(self, email, action):
        """
        Evaluate agent action using easy grader.
        """
        return grade(email, action)