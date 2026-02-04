import os
import sys
import urllib.request

# set paths
base_dir = os.path.dirname(os.path.abspath(__file__))
voices_dir = os.path.join(base_dir, "models", "voices")
os.makedirs(voices_dir, exist_ok=True)

# URLs from Hugging Face for Piper voice en_US-amy-medium
MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

model_file = os.path.join(voices_dir, "en_US-amy-medium.onnx")
config_file = os.path.join(voices_dir, "en_US-amy-medium.onnx.json")

def download(url, filename):
    print(f"Downloading {url} → {filename}")
    urllib.request.urlretrieve(url, filename)
    print("Done.")

def main():
    # download if not already present
    if not os.path.isfile(model_file):
        download(MODEL_URL, model_file)
    else:
        print(f"Model file already exists: {model_file}")
    if not os.path.isfile(config_file):
        download(CONFIG_URL, config_file)
    else:
        print(f"Config file already exists: {config_file}")
    print("All done. Models are in", voices_dir)

if __name__ == "__main__":
    main()
