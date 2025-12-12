import os
import google.generativeai as genai
import PIL.Image

def image_to_yaml(image_path):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    genai.configure(api_key=api_key)
    # Using gemini-2.0-flash as tested
    model = genai.GenerativeModel('gemini-2.0-flash')

    try:
        img = PIL.Image.open(image_path)
    except Exception as e:
        raise ValueError(f"Could not open image {image_path}: {e}")

    prompt = """
You are an expert in converting diagram images into a specific YAML format used by 'widip'.
The YAML format represents a string diagram.
Here is an example of the YAML for this specific diagram style:
---
- !crack egg: { white, yolk }
  !crack egg: { white, yolk }
- !whisk { white, white }: whisked whites
  !beat { yolk, yolk, sugar }: yolky paste
- !stir { yolky paste, mascarpone }: thick paste
- !fold { whisked whites, thick paste }: crema di mascarpone
---

Please convert the provided image into this YAML format.
Only output the YAML code, no other text. Ensure the output starts with '---' if appropriate or just the list of actions.
The output should be directly parsable by the widip loader.
"""

    response = model.generate_content([prompt, img])
    text = response.text.strip()

    # Clean up markdown code blocks if present
    if text.startswith("```yaml"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()
