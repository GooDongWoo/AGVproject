#!/usr/bin/env python
# coding: utf-8

"""
AGV 설정 파일 - JSON 송수신 기능 포함
"""

import numpy as np

# AGV 식별 설정
AGV_ID = "1"  # 각 AGV마다 고유 ID 설정 (1, 2, 3 등)

# MQTT 설정
MQTT_BROKER_ADDRESS = "192.168.0.22"
MQTT_BROKER_PORT = 1883
COMMAND_TOPIC = f"agv/{AGV_ID}/command"
SENSING_TOPIC = f"agv/{AGV_ID}/sensing"

# 센서 데이터 송신 설정
SENSING_INTERVAL = 0.5  # 0.5초마다 송신

# AI 모델 설정
MODEL_PATH = "../best.pth"
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# 카메라 설정
FRAME_WIDTH = 224
FRAME_HEIGHT = 224
CAMERA_CENTER_X = 112
CAMERA_CENTER_Y = 112

# 영상처리 설정
BLUR_KERNEL_SIZE = (15, 15)
EROSION_ITERATIONS = 2
DILATION_ITERATIONS = 2

# 영역 인식 설정
ARRIVAL_THRESHOLD_X = 15
ARRIVAL_THRESHOLD_Y = 15
AREA_DETECTION_INTERVAL = 0.1

# HSV 색상 범위
COLOR_LIST = ["red", "green", "blue", "purple", "yellow", "orange"]
COLOR_RANGES = [
    {'name': 'red', 'lower': np.array([0, 100, 100]), 'upper': np.array([10, 255, 255])},
    {'name': 'green', 'lower': np.array([40, 50, 50]), 'upper': np.array([80, 255, 255])},
    {'name': 'blue', 'lower': np.array([100, 100, 100]), 'upper': np.array([130, 255, 255])},
    {'name': 'purple', 'lower': np.array([130, 50, 50]), 'upper': np.array([170, 255, 255])},
    {'name': 'yellow', 'lower': np.array([20, 100, 100]), 'upper': np.array([30, 255, 255])},
    {'name': 'orange', 'lower': np.array([10, 100, 100]), 'upper': np.array([20, 255, 255])},
]

# 모터 제어 설정
SPEED_GAIN = 0.17
STEERING_GAIN = 0.2
STEERING_DGAIN = 0.0
STEERING_BIAS = 0.0
ROAD_FOLLOWING_INTERVAL = 0.1

# 서보 모터 설정
SERVO_ACTION_DURATION = 2.0