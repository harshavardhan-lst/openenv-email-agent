import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graders.grader_easy import grade


def test_easy_grader():
    email = {"label": "spam"}

    score = grade(email, "spam")

    assert score == 1.0