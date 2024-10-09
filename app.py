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
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.realesrgan = RealESRGAN(device, scale=4)
        
        if not os.path.isfile(weight_file):
            raise FileNotFoundError(f"Model weights not found at {weight_file}")

        self.realesrgan.load_weights(weight_file)

    @app.api_endpoint
    async def predict(self, url: str):
        try:
            #image = load_image(url).convert('RGB')  # Ensure it's in RGB format
            image = open_image_from_url(url).convert('RGB')

            
            transform = transforms.ToTensor()
            image_tensor = transform(image).unsqueeze(0)  # Add batch dimension

            with torch.no_grad():
                sr_image_tensor = self.realesrgan.predict(image_tensor)  the appropriate method
            
            sr_image = transforms.ToPILImage()(sr_image_tensor.squeeze(0)) 

            s3 = S3Handler()
            upload_url = await s3.upload_images([sr_image])

            return {'images': upload_url}

        except Exception as e:
            print(f"Error: {e}")
            return {"error": f"Image generation failed: {str(e)}"}

server = Server(app)
server.run()

