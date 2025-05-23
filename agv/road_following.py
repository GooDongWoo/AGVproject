#!/usr/bin/env python
# coding: utf-8

"""
도로 추종 - 핵심 기능만
"""

import threading
import time
import numpy as np
import torch
import torchvision.transforms as transforms
import PIL.Image
from config import *

class RoadFollowing(threading.Thread):
    def __init__(self, camera, robot, model, mean, std):
        super().__init__()
        self.camera = camera
        self.robot = robot
        self.model = model
        self.mean = mean
        self.std = std
        
        self.th_flag = True
        self.is_active = False
        self.angle_last = 0.0
        
    def run(self):
        while self.th_flag:
            if not self.is_active:
                time.sleep(ROAD_FOLLOWING_INTERVAL)
                continue
                
            try:
                image = self.camera.value
                if image is None:
                    time.sleep(ROAD_FOLLOWING_INTERVAL)
                    continue
                    
                xy = self.model(self._preprocess(image)).detach().float().cpu().numpy().flatten()
                x = xy[0]
                y = (0.5 - xy[1]) / 2.0
                
                angle = np.arctan2(x, y)
                pid = (angle * STEERING_GAIN + (angle - self.angle_last) * STEERING_DGAIN)
                self.angle_last = angle
                
                final_steering = pid + STEERING_BIAS
                final_steering = np.clip(final_steering, -1.0, 1.0)
                
                left_speed = np.clip(SPEED_GAIN + final_steering, 0.0, 1.0)
                right_speed = np.clip(SPEED_GAIN - final_steering, 0.0, 1.0)
                
                self.robot.left_motor.value = left_speed
                self.robot.right_motor.value = right_speed
                
            except:
                self.robot.stop()
                
            time.sleep(ROAD_FOLLOWING_INTERVAL)
        
        self.robot.stop()
    
    def _preprocess(self, image):
        try:
            image = PIL.Image.fromarray(image)
            image = transforms.functional.to_tensor(image).to('cuda').half()
            image.sub_(self.mean[:, None, None]).div_(self.std[:, None, None])
            return image[None, ...]
        except:
            return None
    
    def start_following(self):
        self.is_active = True
    
    def stop_following(self):
        self.is_active = False
        self.robot.stop()
    
    def stop(self):
        self.th_flag = False
        self.is_active = False
        self.robot.stop()