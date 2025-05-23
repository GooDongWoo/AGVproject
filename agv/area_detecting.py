#!/usr/bin/env python
# coding: utf-8

"""
작업영역 탐지 - 로봇팔 통합 (item_idx 지원)
"""

import threading
import time
import cv2
import numpy as np
import sys
import os

# 로봇팔 제어 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), 'control'))
from control.JBArm import JBArm
from control.BoxDetector import BoxDetector

from config import *

class AreaDetection(threading.Thread):
    def __init__(self, camera, road_following_controller=None):
        super().__init__()
        self.camera = camera
        self.road_following_controller = road_following_controller
        
        self.th_flag = True
        self.is_active = False
        self.current_phase = 1  # 1: 집하장소, 2: 배송장소
        
        self.start_area_color = None
        self.end_area_color = None
        self.grip_done = False
        
        # 물건 인덱스
        self.item_idx = 0
        
        # 로봇팔 및 물건 탐지 초기화
        self.robot_arm = None
        self.box_detector = None
        self._init_robot_arm()
        
        self.arrival_callback = None
        self.task_complete_callback = None
        
    def _init_robot_arm(self):
        """로봇팔 및 물건 탐지 시스템 초기화"""
        try:
            if ROBOT_ARM_ENABLED:
                print("로봇팔 초기화 중...")
                self.robot_arm = JBArm()
                self.box_detector = BoxDetector()
                print("✅ 로봇팔 초기화 완료")
            else:
                print("⚠️ 로봇팔 비활성화됨")
        except Exception as e:
            print(f"❌ 로봇팔 초기화 실패: {e}")
            self.robot_arm = None
            self.box_detector = None
        
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
                    self._detect_area(hsv, self.start_area_color, is_pickup=True)
                elif self.current_phase == 2:
                    self._detect_area(hsv, self.end_area_color, is_pickup=False)
                    
            except Exception as e:
                print(f"영역 탐지 오류: {e}")
                
            time.sleep(AREA_DETECTION_INTERVAL)
    
    def _detect_area(self, hsv, color_info, is_pickup=True):
        """영역 탐지 및 로봇팔 동작"""
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
                    self._handle_pickup_area()
                elif self.current_phase == 2:
                    self._handle_delivery_area()
    
    def _handle_pickup_area(self):
        """집하 영역 도착 처리"""
        print(f"🎯 집하 영역 도착 - 물건 {self.item_idx}")
        
        # 1. 로드 팔로잉 정지
        self._stop_road_following()
        
        # 2. 물건 탐지 및 집기
        if self._pickup_object():
            # 3. 다음 단계로 전환
            self._switch_to_phase2()
            
            # 4. 로드 팔로잉 재시작
            self._start_road_following()
        else:
            print("❌ 물건 집기 실패")
            # 실패 시 로드 팔로잉 재시작
            self._start_road_following()
    
    def _handle_delivery_area(self):
        """배송 영역 도착 처리"""
        print(f"🎯 배송 영역 도착 - 물건 {self.item_idx}")
        
        # 1. 로드 팔로잉 정지
        self._stop_road_following()
        
        # 2. 물건 놓기
        if self._place_object():
            # 3. 작업 완료
            self._complete_task()
        else:
            print("❌ 물건 놓기 실패")
            self._complete_task()  # 실패해도 작업 완료로 처리
    
    def _pickup_object(self):
        """물건 집기 동작"""
        if not self.robot_arm or not self.box_detector:
            print("⚠️ 로봇팔 또는 물건 탐지 시스템 없음")
            time.sleep(ARM_OPERATION_DELAY)
            return True  # 시뮬레이션
        
        try:
            print(f"🔍 물건 {self.item_idx} 탐지 시작...")
            
            # 물건 위치 탐지 (ArUco 마커 기반)
            object_position = self._detect_object_position()
            
            if object_position is not None:
                print(f"📍 물건 {self.item_idx} 위치: {object_position}")
                
                # 로봇팔로 집기
                self.robot_arm.pick(object_position)
                self.grip_done = True
                
                print(f"✅ 물건 {self.item_idx} 집기 완료")
                return True
            else:
                print(f"❌ 물건 {self.item_idx} 탐지 실패")
                return False
                
        except Exception as e:
            print(f"물건 집기 오류: {e}")
            return False
    
    def _place_object(self):
        """물건 놓기 동작"""
        if not self.robot_arm:
            print("⚠️ 로봇팔 시스템 없음")
            time.sleep(ARM_OPERATION_DELAY)
            return True  # 시뮬레이션
        
        try:
            print(f"📦 물건 {self.item_idx} 놓기 시작...")
            
            # 현재 위치에서 약간 앞쪽에 놓기
            place_position = np.array([200, 0, 50])  # 기본 놓기 위치
            
            # 로봇팔로 놓기
            self.robot_arm.place(place_position)
            
            print(f"✅ 물건 {self.item_idx} 놓기 완료")
            return True
            
        except Exception as e:
            print(f"물건 놓기 오류: {e}")
            return False
    
    def _detect_object_position(self):
        """ArUco 마커 기반 물건 위치 탐지"""
        if not self.box_detector:
            return None
        
        for attempt in range(MARKER_DETECTION_RETRIES):
            try:
                # 카메라에서 이미지 획득
                frame = self.camera.value
                if frame is None:
                    continue
                
                # 이미지 크기 조정
                frame_resized = cv2.resize(frame, (300, 300), interpolation=cv2.INTER_LINEAR)
                
                # 박스 탐지
                detected_boxes = self.box_detector.detect_boxes(frame_resized)
                
                # 물건 인덱스와 일치하는 마커 찾기
                if self.item_idx in detected_boxes:
                    object_position = detected_boxes[self.item_idx]
                    print(f"🎯 마커 {self.item_idx} 탐지 성공: {object_position}")
                    return object_position
                
                print(f"⏳ 시도 {attempt + 1}/{MARKER_DETECTION_RETRIES} - 마커 {self.item_idx} 미발견")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"물건 탐지 오류 (시도 {attempt + 1}): {e}")
        
        print(f"❌ 마커 {self.item_idx} 탐지 실패 - 모든 시도 소진")
        return None
    
    def _stop_road_following(self):
        """로드 팔로잉 정지"""
        if self.road_following_controller:
            self.road_following_controller.stop_following()
            print("⏸️ 로드 팔로잉 정지")
        time.sleep(0.5)  # 완전 정지 대기
    
    def _start_road_following(self):
        """로드 팔로잉 시작"""
        if self.road_following_controller:
            self.road_following_controller.start_following()
            print("▶️ 로드 팔로잉 재시작")
        time.sleep(0.5)  # 시작 대기
    
    def _switch_to_phase2(self):
        """2단계로 전환"""
        self.current_phase = 2
        print(f"🔄 물건 {self.item_idx} - 2단계(배송)로 전환")
    
    def _complete_task(self):
        """작업 완료"""
        print(f"🏁 물건 {self.item_idx} 작업 완료")
        self.is_active = False
        if self.task_complete_callback:
            self.task_complete_callback()
    
    def set_target_areas(self, start_color_name, end_color_name):
        """목표 영역 설정"""
        self.start_area_color = self._get_color_info(start_color_name)
        self.end_area_color = self._get_color_info(end_color_name)
        print(f"🎯 목표 영역 설정: {start_color_name} → {end_color_name}")
    
    def set_item_index(self, item_idx):
        """물건 인덱스 설정"""
        self.item_idx = item_idx
        print(f"📦 물건 인덱스 설정: {item_idx}")
    
    def set_road_following_controller(self, controller):
        """로드 팔로잉 컨트롤러 설정"""
        self.road_following_controller = controller
        print("🛣️ 로드 팔로잉 컨트롤러 연결됨")
    
    def _get_color_info(self, color_name):
        """색상 정보 반환"""
        return next((color for color in COLOR_RANGES if color['name'] == color_name), None)
    
    def start_detection(self):
        """탐지 시작"""
        self.is_active = True
        self.current_phase = 1
        self.grip_done = False
        print(f"🔍 물건 {self.item_idx} 영역 탐지 시작")
    
    def stop_detection(self):
        """탐지 정지"""
        self.is_active = False
        print(f"⏹️ 물건 {self.item_idx} 영역 탐지 정지")
    
    def stop(self):
        """스레드 종료"""
        self.th_flag = False
        self.is_active = False
        
        # 로봇팔 안전 위치로 이동
        if self.robot_arm:
            try:
                self.robot_arm.ready()
                print("🏠 로봇팔 안전 위치로 이동")
            except:
                pass
        
        print("⏹️ 영역 탐지 스레드 종료")
    
    def set_callbacks(self, task_complete_callback=None):
        """콜백 함수 설정"""
        self.task_complete_callback = task_complete_callback