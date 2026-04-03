# OpenEnv Email Agent

A project for evaluating email agents with tasks of varying difficulty, environments, and graders.

## Structure
- `env/`: Environment and models.
- `tasks/`: Easy, medium, hard tasks.
- `graders/`: Corresponding graders.
- `data/emails.json`: Sample emails.
- `demo/app.py`: Streamlit demo.
- `inference.py`: Main inference script.
- `tests/`: Unit tests.

## Setup
1. `pip install -r requirements.txt`
2. Run `streamlit run demo/app.py` for demo.

## Usage
See `inference.py` for running evaluations.

