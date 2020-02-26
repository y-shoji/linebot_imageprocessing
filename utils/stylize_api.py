import torch
import utils
import transformer
import os
from torchvision import transforms
import cv2

class stylize_api:
    def __init__(self,mode="tokyo_ghoul"):
        self.mode = f"static/pth/{mode}.pth"
        if not os.path.isfile(self.mode):
            self.mode = "static/pth/tokyo_ghoul.pth"

        self.device = ("cuda" if torch.cuda.is_available() else "cpu")
        self.net = transformer.TransformerNetwork()
        self.net.load_state_dict(torch.load(self.mode, map_location={'cuda:0': 'cpu'}))
        self.net = self.net.to(self.device)

        self.PRESERVE_COLOR = False

    def stylzie(self,img):
        torch.cuda.empty_cache()
        content_tensor = utils.itot(img).to(self.device)
        generated_tensor = self.net(content_tensor)
        generated_image = utils.ttoi(generated_tensor.detach())
        if self.PRESERVE_COLOR:
            generated_image = utils.transfer_color(img, generated_image)
        
        return generated_image.clip(0, 255)
