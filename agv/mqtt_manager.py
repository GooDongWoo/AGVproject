#!/usr/bin/env python
# coding: utf-8

"""
MQTT 통신 관리 - 새로운 JSON 포맷 적용
"""

import paho.mqtt.client as mqtt
import json
import threading
import time
import base64
import cv2
import random
from datetime import datetime
from config import *

class MQTTManager:
    def __init__(self, command_callback=None, camera=None):
        self.client = None
        self.is_connected = False
        self.command_callback = command_callback
        self.camera = camera
        
        # 송신 관련
        self.is_task_running = False
        self.is_finished = False
        self.sensing_thread = None
        self.sensing_thread_flag = False
        
        # 작업 상태 관리
        self.current_work_id = None
        self.work_started = False
        self.collision_occurred = False
        
    def connect(self):
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            
            self.client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, 60)
            self.client.loop_start()
            return True
        except:
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            client.subscribe(COMMAND_TOPIC, 1)
            print(f"MQTT 연결 성공 및 토픽 구독: {COMMAND_TOPIC}")
        else:
            self.is_connected = False
            print(f"MQTT 연결 실패: {rc}")
    
    def _convert_location_to_string(self, location):
        """위치 데이터를 문자열로 변환"""
        try:
            if isinstance(location, str):
                if location in COLOR_LIST:
                    return location
                else:
                    print(f"알 수 없는 색상명: {location}")
                    return None
            
            elif isinstance(location, int):
                if 0 <= location < len(COLOR_LIST):
                    color_name = COLOR_LIST[location]
                    print(f"정수 {location} -> 색상 '{color_name}'으로 변환")
                    return color_name
                else:
                    print(f"색상 인덱스 범위 초과: {location}")
                    return None
            
            else:
                print(f"지원하지 않는 위치 데이터 타입: {type(location)}")
                return None
                
        except Exception as e:
            print(f"위치 변환 오류: {e}")
            return None
    
    def _on_message(self, client, userdata, msg):
        try:
            command_data = json.loads(msg.payload.decode("utf-8"))
            print(f"원본 명령 수신: {command_data}")
            
            # 필수 필드 확인
            required_fields = ["timedata", "start", "end", "delays", "item_idx"]
            if not all(field in command_data for field in required_fields):
                print("필수 필드 누락된 명령 무시")
                return
            
            # 위치 데이터 변환
            start_location = self._convert_location_to_string(command_data["start"])
            end_location = self._convert_location_to_string(command_data["end"])
            
            if start_location is None or end_location is None:
                print("위치 데이터 변환 실패 - 명령 무시")
                return
            
            # 변환된 데이터로 새 명령 생성
            converted_command = {
                "timedata": command_data["timedata"],
                "start": start_location,
                "end": end_location,
                "delays": command_data["delays"],
                "item_idx": command_data["item_idx"]
            }
            
            print(f"변환된 명령: {converted_command}")
            
            if self.command_callback:
                self.command_callback(converted_command)
                
        except Exception as e:
            print(f"명령 처리 오류: {e}")
    
    def start_sensing_transmission(self):
        """센서 데이터 송신 시작 (0.5초마다)"""
        if self.sensing_thread and self.sensing_thread.is_alive():
            return
            
        self.is_task_running = True
        self.is_finished = False
        self.sensing_thread_flag = True
        
        # 작업 시작 시 새로운 workId 생성
        self.current_work_id = random.randint(100000, 999999)
        self.work_started = False
        self.collision_occurred = False
        
        self.sensing_thread = threading.Thread(target=self._sensing_loop)
        self.sensing_thread.daemon = True
        self.sensing_thread.start()
        print(f"센서 데이터 송신 시작 - Work ID: {self.current_work_id}")
    
    def stop_sensing_transmission(self):
        """센서 데이터 송신 정지"""
        self.sensing_thread_flag = False
        self.is_task_running = False
        
        if self.sensing_thread and self.sensing_thread.is_alive():
            self.sensing_thread.join(timeout=1.0)
        print("센서 데이터 송신 정지")
    
    def set_task_finished(self):
        """작업 완료 상태 설정"""
        self.is_finished = True
    
    def trigger_collision(self):
        """충돌 발생 신호"""
        self.collision_occurred = True
        print("충돌 발생 감지")
    
    def _sensing_loop(self):
        """0.5초마다 센서 데이터 송신하는 루프"""
        while self.sensing_thread_flag and self.is_task_running:
            try:
                self._send_sensing_data()
                time.sleep(0.5)
            except Exception as e:
                print(f"센서 데이터 송신 오류: {e}")
                time.sleep(0.5)
    
    def _send_sensing_data(self):
        """센서 데이터 송신 - 새로운 JSON 포맷"""
        if not self.is_connected:
            return
            
        try:
            # 현재 시간
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 카메라에서 이미지 획득
            image_b64 = None
            if self.camera and self.camera.value is not None:
                _, buffer = cv2.imencode('.jpg', self.camera.value)
                image_b64 = base64.b64encode(buffer).decode('utf-8')
            
            # cmd_string 결정
            cmd_string = None
            if not self.work_started:
                # 작업 시작
                cmd_string = "start"
                self.work_started = True
                print(f"작업 시작 신호 전송 - Work ID: {self.current_work_id}")
            elif self.collision_occurred:
                # 충돌 발생
                cmd_string = "col"
                self.collision_occurred = False  # 충돌 신호 리셋
                print(f"충돌 신호 전송 - Work ID: {self.current_work_id}")
            elif self.is_finished:
                # 작업 완료
                cmd_string = "end"
                print(f"작업 완료 신호 전송 - Work ID: {self.current_work_id}")
            else:
                # 작업 중
                cmd_string = None
            
            # 새로운 JSON 데이터 구성
            sensing_data = {
                "agvId": int(AGV_ID),
                "workId": self.current_work_id,
                "cmd_string": cmd_string,
                "time": current_time,
                "image": image_b64,
                "box_idx": 0,  # 필요시 실제 box_idx 값으로 업데이트
                "is_finished": 1 if self.is_finished else 0
            }
            
            # MQTT로 송신
            json_data = json.dumps(sensing_data)
            self.client.publish(SENSING_TOPIC, json_data, 1)
            
            # 로그 출력 (cmd_string이 있을 때만)
            if cmd_string:
                print(f"센싱 데이터 전송: cmd_string={cmd_string}, workId={self.current_work_id}")
            
            if self.is_finished:
                print("작업 완료 - 센서 데이터 송신 종료")
                self.sensing_thread_flag = False
                
        except Exception as e:
            print(f"센서 데이터 생성/송신 오류: {e}")
    
    def set_box_index(self, box_idx):
        """박스 인덱스 설정"""
        self.box_idx = box_idx
    
    def disconnect(self):
        """연결 종료"""
        self.stop_sensing_transmission()
        
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            print("MQTT 연결 종료")