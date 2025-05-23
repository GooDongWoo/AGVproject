#!/usr/bin/env python
# coding: utf-8

"""
작업영역 탐지 - 핵심 기능만
"""

import threading
import time
import cv2
import numpy as np
from config import *

class AreaDetection(threading.Thread):
    def __init__(self, camera, servo_controller=None):
        super().__init__()
        self.camera = camera
        self.servo_controller = servo_controller
        
        self.th_flag = True
        self.is_active = False
        self.current_phase = 1  # 1: 집하장소, 2: 배송장소
        
        self.start_area_color = None
        self.end_area_color = None
        self.grip_done = False
        
        self.arrival_callback = None
        self.task_complete_callback = None
        
    def run(self):
        while self.th_flag:
            if not self.is_active or not self.start_area_color or not self.end_area_color:
                time.sleep(AREA_DETECTION_INTERVAL)
                continue
                
            try:
                image_input = self.camera.value
                if image_input is None:
                    time.sleep(AREA_DETECTION_INTERVAL)
                    continue
                    
                hsv = cv2.cvtColor(image_input, cv2.COLOR_BGR2HSV)
                hsv = cv2.blur(hsv, BLUR_KERNEL_SIZE)
                
                if self.current_phase == 1:
                    self._detect_area(hsv, self.start_area_color)
                elif self.current_phase == 2:
                    self._detect_area(hsv, self.end_area_color)
                    
            except:
                pass
                
            time.sleep(AREA_DETECTION_INTERVAL)
    
    def _detect_area(self, hsv, color_info):
        if not color_info:
            return
            
        mask = cv2.inRange(hsv, color_info['lower'], color_info['upper'])
        mask = cv2.erode(mask, None, iterations=EROSION_ITERATIONS)
        mask = cv2.dilate(mask, None, iterations=DILATION_ITERATIONS)
        
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
            
            if area < 500:
                return
                
            ((box_x, box_y), radius) = cv2.minEnclosingCircle(c)
            X, Y = int(box_x), int(box_y)
            
            error_X = abs(CAMERA_CENTER_X - X)
            error_Y = abs(CAMERA_CENTER_Y - Y)
            
            if error_X < ARRIVAL_THRESHOLD_X and error_Y < ARRIVAL_THRESHOLD_Y:
                if self.current_phase == 1 and not self.grip_done:
                    self._do_grip()
                    self._switch_to_phase2()
                elif self.current_phase == 2:
                    self._do_release()
                    self._complete_task()
    
    def _do_grip(self):
        if self.servo_controller:
            self.servo_controller.grip()
        else:
            time.sleep(SERVO_ACTION_DURATION)
        self.grip_done = True
    
    def _do_release(self):
        if self.servo_controller:
            self.servo_controller.release()
        else:
            time.sleep(SERVO_ACTION_DURATION)
    
    def _switch_to_phase2(self):
        self.current_phase = 2
    
    def _complete_task(self):
        self.is_active = False
        if self.task_complete_callback:
            self.task_complete_callback()
    
    def set_target_areas(self, start_color_name, end_color_name):
        self.start_area_color = self._get_color_info(start_color_name)
        self.end_area_color = self._get_color_info(end_color_name)
    
    def _get_color_info(self, color_name):
        return next((color for color in COLOR_RANGES if color['name'] == color_name), None)
    
    def start_detection(self):
        self.is_active = True
        self.current_phase = 1
        self.grip_done = False
    
    def stop_detection(self):
        self.is_active = False
    
    def stop(self):
        self.th_flag = False
        self.is_active = False
    
    def set_callbacks(self, task_complete_callback=None):
        self.task_complete_callback = task_complete_callback