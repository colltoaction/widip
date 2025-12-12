import google.generativeai as genai
import os
import PIL.Image
import sys

# Get the file path from arguments or default to hello-world.jpg
file_path = "examples/hello-world.jpg"
default_prompt = (
    "Suggest improvements to the following diagrammatic representation of the input YAML "
    "or satisfied with the diagram appearence. "
    "Context: The diagrams represent programs using category theory (monoidal, closed, symmetric, markov categories) "
    "and the 'programs as diagrams' paradigm."
)
prompt = default_prompt

if len(sys.argv) > 1:
    # Check if arg is a file path
    if sys.argv[1].endswith(".jpg") or sys.argv[1].endswith(".png"):
        file_path = sys.argv[1]
        if len(sys.argv) > 2:
            prompt = " ".join(sys.argv[2:]) + "\n\n" + default_prompt
    else:
        # arg is prompt, use default file
        prompt = " ".join(sys.argv[1:]) + "\n\n" + default_prompt

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')
try:
    img = PIL.Image.open(file_path)
    response = model.generate_content([prompt, img])
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
