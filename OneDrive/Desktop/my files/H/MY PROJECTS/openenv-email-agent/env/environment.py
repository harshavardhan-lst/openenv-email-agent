import json
import random
from pathlib import Path
from tasks.easy_task import EasyTask


class EmailEnv:
    """
    OpenEnv-style environment for email triage.
    """

    def __init__(self, data_path="data/emails.json"):

        path = Path(data_path)

        with open(path, "r") as f:
            self.emails = json.load(f)

        self.current_index = 0
        self.total_reward = 0
        self.history = []

        # define task
        self.task = EasyTask()

    def reset(self):
        """
        Starts a new episode.
        """

        random.shuffle(self.emails)

        self.current_index = 0
        self.total_reward = 0
        self.history = []

        return self._get_observation()

    def step(self, action):
        """
        Executes one environment step.
        """

        email = self.emails[self.current_index]

        # evaluate action
        reward = self.task.evaluate(email, action)

        self.total_reward += reward

        self.history.append({
            "email": email,
            "action": action,
            "reward": reward
        })

        self.current_index += 1

        done = self.current_index >= len(self.emails)

        if done:
            observation = None
        else:
            observation = self._get_observation()

        info = {
            "total_reward": self.total_reward
        }

        return observation, reward, done, info

    def state(self):
        """
        Returns internal environment state.
        """

        return {
            "current_index": self.current_index,
            "processed_emails": len(self.history),
            "total_reward": self.total_reward
        }

    def _get_observation(self):
        """
        Returns the current email observation.
        """

        email = self.emails[self.current_index]

        return {
            "email_id": email["email_id"],
            "sender": email["sender"],
            "subject": email["subject"],
            "body": email["body"]
        }