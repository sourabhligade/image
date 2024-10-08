from pydantic import BaseModel, Field
from jarvislabs import App, Server, S3Handler
import torch
import numpy as np
from PIL import Image
import os
from RealESRGAN import RealESRGAN
from diffusers.utils import load_image
from torchvision import transforms
import subprocess

app = App("Real-ESRGAN")

model_path = "models/"
weight_file = os.path.join(model_path, "RealESRGAN_x4plus.pth")

# # Download weights if they don't exist
# if not os.path.exists(weight_file):
#     print("Downloading Real-ESRGAN weights...")
#     subprocess.run(["wget", "-O", weight_file, "https://your_wget_link_for_weights"])
# else:
#     print("Weights already downloaded.")

@app
class ESRGAN:
    @app.setup
    def setup(self):
        # Initialize the Real-ESRGAN model
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.realesrgan = RealESRGAN(device, scale=4)
        
        # Check if weights file exists before loading
        if not os.path.isfile(weight_file):
            raise FileNotFoundError(f"Model weights not found at {weight_file}")

        self.realesrgan.load_weights(weight_file)
        #self.realesrgan.eval()  # Set to evaluation mode

    @app.api_endpoint
    async def predict(self, url: str):
        images = []  # Initialize an empty list to store processed images

        # Change from 'request.image_url' to 'url'
        image = load_image(url)

        try:
            with torch.no_grad():  # Fix indentation
                # Process the single loaded image instead of iterating over a directory
                sr_image = self.realesrgan.predict(image)  # Adjust to the correct method call
                images.append(sr_image)  # Collect the processed image

            s3 = S3Handler()
            upload_url = await s3.upload_images(images)

            return {'images': upload_url}

        except Exception as e:
            print(str(e))
            return {"error": f"Image generation failed: {str(e)}"}

# Run the FastAPI application
server = Server(app)
server.run()
