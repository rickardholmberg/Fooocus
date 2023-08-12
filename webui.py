import gradio as gr
import random
import fooocus_version

from modules.sdxl_styles import apply_style, style_keys, aspect_ratios
from modules.default_pipeline import process
from modules.cv2win32 import save_image
from modules.util import generate_temp_filename
from modules.path import temp_outputs_path


def generate_clicked(prompt, negative_prompt, style_selction, performance_selction,
                     aspect_ratios_selction, image_number, image_seed, progress=gr.Progress()):

    p_txt, n_txt = apply_style(style_selction, prompt, negative_prompt)

    if performance_selction == 'Speed':
        steps = 30
        switch = 20
    else:
        steps = 60
        switch = 40

    width, height = aspect_ratios[aspect_ratios_selction]

    results = []
    seed = image_seed
    if not isinstance(seed, int) or seed < 0 or seed > 65535:
        seed = random.randint(1, 65535)

    all_steps = steps * image_number

    def callback(step, x0, x, total_steps):
        done_steps = i * steps + step
        progress(float(done_steps) / float(all_steps), f'Step {step}/{total_steps} in the {i}-th Sampling')

    for i in range(image_number):
        imgs = process(p_txt, n_txt, steps, switch, width, height, seed, callback=callback)

        for x in imgs:
            local_temp_filename = generate_temp_filename(folder=temp_outputs_path, extension='png')
            save_image(local_temp_filename, x)

        seed += 1
        results += imgs

    return results


block = gr.Blocks(title='Fooocus ' + fooocus_version.version).queue()
with block:
    with gr.Row():
        with gr.Column():
            gallery = gr.Gallery(label='Gallery', show_label=False, object_fit='contain', height=720)
            with gr.Row():
                with gr.Column(scale=0.85):
                    prompt = gr.Textbox(show_label=False, placeholder="Type prompt here.", container=False, autofocus=True)
                with gr.Column(scale=0.15, min_width=0):
                    run_button = gr.Button(label="Generate", value="Generate")
            with gr.Row():
                advanced_checkbox = gr.Checkbox(label='Advanced', value=False, container=False)
        with gr.Column(scale=0.5, visible=False) as right_col:
            with gr.Tab(label='Generator Setting'):
                performance_selction = gr.Radio(label='Performance', choices=['Speed', 'Quality'], value='Speed')
                aspect_ratios_selction = gr.Radio(label='Aspect Ratios (width × height)', choices=list(aspect_ratios.keys()),
                                                  value='1152×896')
                image_number = gr.Slider(label='Image Number', minimum=1, maximum=32, step=1, value=2)
                image_seed = gr.Number(label='Random Seed', value=-1, precision=0)
                negative_prompt = gr.Textbox(label='Negative Prompt', show_label=True, placeholder="Type prompt here.")
            with gr.Tab(label='Image Style'):
                style_selction = gr.Radio(show_label=False, container=True,
                                          choices=style_keys, value='cinematic-default')
        advanced_checkbox.change(lambda x: gr.update(visible=x), advanced_checkbox, right_col)
        ctrls = [
            prompt, negative_prompt, style_selction,
            performance_selction, aspect_ratios_selction, image_number, image_seed
        ]
        run_button.click(fn=generate_clicked, inputs=ctrls, outputs=[gallery])

block.launch(inbrowser=True)
