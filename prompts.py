import json

def get_system_prompt():
    with open('traits.json') as f:
        traits = json.load(f)
    base_prompt = "You are an expert coder and developer."
    traits_prompt = json.dumps(traits, indent=2)
    return f"{base_prompt}\n\nCharacter Traits:\n{traits_prompt}"
