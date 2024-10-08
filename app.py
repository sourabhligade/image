from pydantic import BaseModel, Field
from jarvislabs import App, Server, S3Handler
import torch
from PIL import Image
import os
from RealESRGAN import RealESRGAN
from diffusers.utils import load_image
from torchvision import transforms
import subprocess
import requests
from io import BytesIO



app = App("Real-ESRGAN")

# Define paths directly in the code for simplicity
weight_file = "models/RealESRGAN_x4plus.pth"

def open_image_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        return image
    return None

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

    @app.api_endpoint
    async def predict(self, url: str):
        try:
            # Load and preprocess the image from the URL
            #image = load_image(url).convert('RGB')  # Ensure it's in RGB format
            image = open_image_from_url(url).convert('RGB')

            
            # Convert the image to a tensor
            transform = transforms.ToTensor()
            image_tensor = transform(image).unsqueeze(0)  # Add batch dimension

            # Perform super-resolution with RealESRGAN
            with torch.no_grad():
                sr_image_tensor = self.realesrgan.predict(image_tensor)  # Use the appropriate method
            
            # Convert the result back to a PIL image for saving/upload
            sr_image = transforms.ToPILImage()(sr_image_tensor.squeeze(0))  # Remove batch dimension

            # Upload the processed image to S3
            s3 = S3Handler()
            upload_url = await s3.upload_images([sr_image])

            return {'images': upload_url}

        except Exception as e:
            print(f"Error: {e}")
            return {"error": f"Image generation failed: {str(e)}"}

# Run the FastAPI application
server = Server(app)
server.run()
