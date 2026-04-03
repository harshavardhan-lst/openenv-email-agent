import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import gradio as gr
from env.environment import EmailEnv

# Initialize environment
env = EmailEnv()
current_obs = env.reset()


def process_action(action):
    global current_obs

    obs, reward, done, info = env.step(action)

    if done:
        message = "Inbox finished!"
        current_obs = None
    else:
        current_obs = obs
        message = f"Reward: {reward}"

    return current_obs, message


def reset_env():
    global current_obs
    current_obs = env.reset()
    return current_obs, "Environment reset."


with gr.Blocks() as demo:

    gr.Markdown("# 📧 Email Inbox Management Environment")

    email_display = gr.JSON(label="Current Email")

    action_input = gr.Dropdown(
        choices=["delete_email", "archive_email", "mark_important"],
        label="Choose Action"
    )

    result_output = gr.Textbox(label="Result")

    submit_btn = gr.Button("Submit Action")
    reset_btn = gr.Button("Reset Environment")

    submit_btn.click(
        process_action,
        inputs=action_input,
        outputs=[email_display, result_output]
    )

    reset_btn.click(
        reset_env,
        outputs=[email_display, result_output]
    )

    demo.load(lambda: (current_obs, "Environment started"),
              outputs=[email_display, result_output])

demo.launch()