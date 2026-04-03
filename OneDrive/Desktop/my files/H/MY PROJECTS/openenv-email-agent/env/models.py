from pydantic import BaseModel


class Observation(BaseModel):
    """
    What the agent sees from the environment.
    """

    email_id: int
    sender: str
    subject: str
    body: str


class Action(BaseModel):
    """
    What the agent sends to the environment.
    """

    email_id: int
    action_type: str