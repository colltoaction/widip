import google.generativeai as genai
import os
import PIL.Image
import sys

# Get the file path from arguments or default to hello-world.jpg
file_path = "examples/hello-world.jpg"
prompt = "Suggest improvements to the following diagrammatic representation of the input YAML or satisfied with the diagram appearence wrt programs as diagrams, category theory, monoidal, closed, symmetric, markov"

if len(sys.argv) > 1:
    # Check if arg is a file path
    if sys.argv[1].endswith(".jpg") or sys.argv[1].endswith(".png"):
        file_path = sys.argv[1]
        if len(sys.argv) > 2:
            prompt = " ".join(sys.argv[2:])
    else:
        # arg is prompt, use default file
        prompt = " ".join(sys.argv[1:])

# Read YAML content
yaml_path = file_path.replace(".jpg", ".yaml").replace(".png", ".yaml")
yaml_content = ""
try:
    with open(yaml_path, 'r') as f:
        yaml_content = f.read()
    prompt += f"\n\nInput YAML:\n{yaml_content}"
except Exception as e:
    print(f"Warning: Could not read YAML file {yaml_path}: {e}")

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('models/gemini-3-pro-image-preview')
try:
    img = PIL.Image.open(file_path)
    response = model.generate_content([prompt, img])
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
