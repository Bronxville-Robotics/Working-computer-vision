""" Detect people wearing masks in videos
"""
from pathlib import Path

import click
import cv2
import torch
from skvideo.io import FFmpegWriter, vreader
from torchvision.transforms import Compose, Resize, ToPILImage, ToTensor

from .common.facedetector import FaceDetector
from .train import MaskDetector


@click.command(help="""
                    modelPath: path to model.ckpt\n
                    videoPath: path to video file to annotate
                    """)
@click.argument('modelpath')

@torch.no_grad()
def tagVideo(modelpath, outputPath=None):
    """ detect if persons in video are wearing masks or not
    """
    model = MaskDetector()
    model.load_state_dict(torch.load(modelpath)['state_dict'], strict=False)
    
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()
    
    faceDetector = FaceDetector(
        prototype='covid-mask-detector/models/deploy.prototxt.txt',
        model='covid-mask-detector/models/res10_300x300_ssd_iter_140000.caffemodel',
    )
    
    transformations = Compose([
        ToPILImage(),
        Resize((100, 100)),
        ToTensor(),
    ])
    
    
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.namedWindow('main', cv2.WINDOW_NORMAL)
    labels = ['No mask', 'Mask']
    cap = cv2.VideoCapture(0)
    labelColor = [(10, 0, 255), (10, 255, 0)]
    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # frame = cv2.flip(frame, 1)
        faces = faceDetector.detect(frame)
        for face in faces:
            try:
                xStart, yStart, width, height = face
                
                # clamp coordinates that are outside of the image
                xStart, yStart = max(xStart, 0), max(yStart, 0)
                
                # predict mask label on extracted face
                faceImg = frame[yStart:yStart+height, xStart:xStart+width]
                output = model(transformations(faceImg).unsqueeze(0).to(device))
                _, predicted = torch.max(output.data, 1)
                
                # draw face frame
                cv2.rectangle(frame,
                            (xStart, yStart),
                            (xStart + width, yStart + height),
                            (126, 65, 64),
                            thickness=2)
                
                # center text according to the face frame
                textSize = cv2.getTextSize(labels[predicted], font, 1, 2)[0]
                textX = xStart + width // 2 - textSize[0] // 2
                
                # draw prediction label
                cv2.putText(frame,
                            labels[predicted],
                            (textX, yStart-20),
                            font, 1, labelColor[predicted], 2)
            except:
                pass
            
        cv2.imshow('main', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
   
    cv2.destroyAllWindows()

# pylint: disable=no-value-for-parameter
if __name__ == '__main__':
    tagVideo()
