#!/bin/bash
# Script to clone the Real-ESRGAN repository with sparse checkout

# Clone the repository without checking out files
git clone --no-checkout https://github.com/ai-forever/Real-ESRGAN.git

# Navigate to the cloned repository
cd Real-ESRGAN/

# Enable sparse checkout
git config core.sparseCheckout true

# Add the specific folder (RealESRGAN/*) to sparse checkout
echo "RealESRGAN/*" >> .git/info/sparse-checkout

# Checkout the 'main' branch with sparse checkout
git checkout main

# Move the 'RealESRGAN' directory to the parent directory
mv RealESRGAN/ ../

rm -rf #!/bin/bash
# Script to clone the Real-ESRGAN repository with sparse checkout

# Clone the repository without checking out files
#git clone --no-checkout https://github.com/ai-forever/Real-ESRGAN.git

# Navigate to the cloned repository
cd Real-ESRGAN/

# Enable sparse checkout
git config core.sparseCheckout true

# Add the specific folder (RealESRGAN/*) to sparse checkout
echo "RealESRGAN/*" >> .git/info/sparse-checkout

# Checkout the 'main' branch with sparse checkout
git checkout main

# Move the 'RealESRGAN' directory to the parent directory
mv RealESRGAN/ ../

# Create the 'models' directory if it doesn't exist
mkdir -p ../models

# Download the weights file into the 'models' directory
wget -O ../models/RealESRGAN_x4plus.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth

# Print completion message
echo "Sparse checkout, move, and weights download completed!"


# Create the 'models' directory if it doesn't exist
mkdir -p ../models



# Download the weights file into the 'models' directory
wget -O ../models/RealESRGAN_x4plus.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth

# Print completion message
echo "Sparse checkout, move, and weights download completed!"
