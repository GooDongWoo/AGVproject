import socket
import json
import time
import base64
import os
from datetime import datetime
import paho.mqtt.client as mqtt

# 서버 연결 설정
SERVER_HOST = '43.200.169.7'
SERVER_PORT = 5000
BUFFER_SIZE = 4096

# MQTT 설정
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# 이미지 저장 경로
IMAGE_SAVE_PATH = "/home/doit/ld/agv_images"

class RaspberryPiBridge:
    def __init__(self):
        self.socket = None
        self.mqtt_client = None
        self.connected_to_server = False
        self.connected_to_mqtt = False
        self.running = False
        
        # AGV별 센싱 데이터 저장
        self.agv_sensing_data = {}
        
        # 이미지 저장 디렉토리 생성
        self.ensure_image_directory()
        
        print("라즈베리파이 브릿지 초기화")
    
    def ensure_image_directory(self):
        """이미지 저장 디렉토리 생성"""
        try:
            if not os.path.exists(IMAGE_SAVE_PATH):
                os.makedirs(IMAGE_SAVE_PATH)
                print(f"이미지 저장 디렉토리 생성: {IMAGE_SAVE_PATH}")
            
            # AGV별 서브디렉토리 생성
            for agv_id in range(1, 5):  # AGV 1-4
                agv_dir = os.path.join(IMAGE_SAVE_PATH, f"agv_{agv_id}")
                if not os.path.exists(agv_dir):
                    os.makedirs(agv_dir)
                    print(f"AGV {agv_id} 이미지 디렉토리 생성: {agv_dir}")
                    
        except Exception as e:
            print(f"이미지 디렉토리 생성 오류: {e}")
    
    def connect_to_server(self):
        """서버에 소켓 연결"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((SERVER_HOST, SERVER_PORT))
            self.socket.settimeout(None)
            self.connected_to_server = True
            print("서버 연결 성공")
            
            # 라즈베리 파이로 식별
            ident_data = {
                "client_type": "raspberry_pi",
                "timestamp": datetime.now().isoformat()
            }
            data_string = json.dumps(ident_data, ensure_ascii=False)
            self.socket.sendall(data_string.encode('utf-8'))
            
            return True
        except Exception as e:
            print(f"서버 연결 오류: {e}")
            self.connected_to_server = False
            return False
    
    def setup_mqtt(self):
        """MQTT 클라이언트 설정"""
        try:
            self.mqtt_client = mqtt.Client(client_id="raspberry_pi_bridge")
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            return True
        except Exception as e:
            print(f"MQTT 설정 오류: {e}")
            return False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT 연결 콜백"""
        if rc == 0:
            print("MQTT 브로커 연결 성공")
            self.connected_to_mqtt = True
            
            # AGV 센싱 데이터 토픽 구독 (AGV 1-4)
            for agv_id in range(1, 5):
                sensing_topic = f"agv/{agv_id}/sensing"
                client.subscribe(sensing_topic, 1)
                print(f"AGV {agv_id} 센싱 토픽 구독: {sensing_topic}")
                
        else:
            print(f"MQTT 브로커 연결 실패: {rc}")
            self.connected_to_mqtt = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT 연결 해제 콜백"""
        print("MQTT 브로커 연결 해제됨")
        self.connected_to_mqtt = False
    
    def on_mqtt_message(self, client, userdata, msg):
        """MQTT 메시지 수신 콜백 - AGV 센싱 데이터 처리"""
        try:
            topic = msg.topic
            message = msg.payload.decode('utf-8')
            
            # 토픽에서 AGV ID 추출 (agv/{agv_id}/sensing)
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3 and topic_parts[0] == 'agv' and topic_parts[2] == 'sensing':
                agv_id = str(topic_parts[1])  # 문자열로 통일
                
                # JSON 데이터 파싱
                sensing_data = json.loads(message)
                print(f"AGV {agv_id} 센싱 데이터 수신: is_finished={sensing_data.get('is_finished', 0)}")
                
                # 센싱 데이터 처리
                self.process_sensing_data(agv_id, sensing_data)
                
        except json.JSONDecodeError as e:
            print(f"센싱 데이터 JSON 파싱 오류: {e}")
        except Exception as e:
            print(f"센싱 데이터 처리 오류: {e}")
    
    def process_sensing_data(self, agv_id, sensing_data):
        """AGV 센싱 데이터 처리"""
        try:
            is_finished = sensing_data.get('is_finished', 0)
            bgr_image_b64 = sensing_data.get('bgr_image', '')
            
            # 현재 시간
            current_time = datetime.now()
            
            # AGV별 센싱 데이터 초기화
            if agv_id not in self.agv_sensing_data:
                self.agv_sensing_data[agv_id] = {
                    'last_update': None,
                    'work_status': 'idle',
                    'start_image_saved': False,
                    'end_image_saved': False,
                    'current_work_id': None
                }
            
            agv_data = self.agv_sensing_data[agv_id]
            
            # 이미지가 있는 경우 저장
            if bgr_image_b64:
                self.save_agv_image(agv_id, bgr_image_b64, is_finished, current_time)
            
            # 작업 상태 변화 감지 및 처리
            if is_finished == 1:
                if agv_data['work_status'] != 'finished':
                    print(f"🏁 AGV {agv_id} 작업 완료!")
                    agv_data['work_status'] = 'finished'
                    agv_data['end_image_saved'] = True
                    
                    # 작업 완료 로그
                    self.log_work_completion(agv_id, current_time)
                    
            elif is_finished == 0:
                if agv_data['work_status'] == 'idle':
                    # 새 작업 시작
                    print(f"🚀 AGV {agv_id} 작업 시작!")
                    agv_data['work_status'] = 'working'
                    agv_data['start_image_saved'] = True
                    agv_data['end_image_saved'] = False
                    agv_data['current_work_id'] = f"{agv_id}_{int(current_time.timestamp())}"
                    
                    # 작업 시작 로그
                    self.log_work_start(agv_id, current_time)
                    
                elif agv_data['work_status'] == 'finished':
                    # 작업 완료 후 대기 상태로 복귀
                    print(f"⏸️ AGV {agv_id} 대기 상태로 복귀")
                    agv_data['work_status'] = 'idle'
                    agv_data['current_work_id'] = None
            
            # 마지막 업데이트 시간 갱신
            agv_data['last_update'] = current_time
            
            # 서버로 상태 정보 전송 (선택적)
            self.send_agv_status_to_server(agv_id, agv_data, is_finished)
            
        except Exception as e:
            print(f"센싱 데이터 처리 중 오류: {e}")
    
    def save_agv_image(self, agv_id, image_b64, is_finished, timestamp):
        """AGV 이미지 저장"""
        try:
            # Base64 디코딩
            image_data = base64.b64decode(image_b64)
            
            # 파일명 생성
            time_str = timestamp.strftime("%Y%m%d_%H%M%S")
            status = "end" if is_finished == 1 else "work"
            filename = f"agv_{agv_id}_{status}_{time_str}.jpg"
            
            # 파일 경로
            agv_dir = os.path.join(IMAGE_SAVE_PATH, f"agv_{agv_id}")
            filepath = os.path.join(agv_dir, filename)
            
            # 이미지 저장
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            print(f"📸 AGV {agv_id} 이미지 저장: {filename}")
            
            # 이미지 크기 확인
            file_size = os.path.getsize(filepath)
            print(f"   이미지 크기: {file_size} bytes")
            
        except Exception as e:
            print(f"이미지 저장 오류: {e}")
    
    def log_work_start(self, agv_id, timestamp):
        """작업 시작 로그"""
        log_entry = {
            "agv_id": str(agv_id),
            "event": "work_start",
            "timestamp": timestamp.isoformat(),
            "work_id": self.agv_sensing_data[agv_id]['current_work_id']
        }
        self.write_log(log_entry)
    
    def log_work_completion(self, agv_id, timestamp):
        """작업 완료 로그"""
        log_entry = {
            "agv_id": str(agv_id),
            "event": "work_complete",
            "timestamp": timestamp.isoformat(),
            "work_id": self.agv_sensing_data[agv_id]['current_work_id']
        }
        self.write_log(log_entry)
    
    def write_log(self, log_entry):
        """로그 파일 작성"""
        try:
            log_file = os.path.join(IMAGE_SAVE_PATH, "agv_work_log.txt")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"로그 작성 오류: {e}")
    
    def send_agv_status_to_server(self, agv_id, agv_data, is_finished):
        """AGV 상태를 서버로 전송 (선택적)"""
        try:
            if not self.connected_to_server:
                return
            
            status_data = {
                "type": "agv_status",
                "agv_id": str(agv_id),
                "status": agv_data['work_status'],
                "is_finished": int(is_finished),
                "timestamp": agv_data['last_update'].isoformat() if agv_data['last_update'] else None,
                "work_id": agv_data.get('current_work_id')
            }
            
            data_string = json.dumps(status_data, ensure_ascii=False)
            self.socket.sendall(data_string.encode('utf-8'))
            print(f"📊 AGV {agv_id} 상태 정보 서버 전송")
            
        except Exception as e:
            print(f"서버 상태 전송 오류: {e}")
    
    def receive_server_commands(self):
        """서버로부터 명령 수신 및 AGV로 전달"""
        if not self.connected_to_server:
            return
        
        try:
            while self.running:
                try:
                    data = self.socket.recv(BUFFER_SIZE)
                    
                    if not data:
                        print("서버 연결 종료")
                        self.connected_to_server = False
                        break
                    
                    command_string = data.decode('utf-8')
                    command = json.loads(command_string)
                    print(f"명령 수신: {command}")
                    
                    # 필수 필드 확인
                    if all(field in command for field in ["agv_id", "start", "end", "delays"]):
                        agv_id = str(command["agv_id"])  # 문자열로 통일
                        
                        # MQTT를 통해 AGV에 명령 전달
                        if self.connected_to_mqtt:
                            mqtt_topic = f"agv/{agv_id}/command"
                            
                            # 명령 데이터 통일된 형식으로 재구성
                            agv_command = {
                                "agv_id": agv_id,
                                "start": command["start"],
                                "end": command["end"],
                                "delays": int(command["delays"]),
                                "timestamp": command.get("timedata", datetime.now().isoformat())
                            }
                            
                            command_json = json.dumps(agv_command, ensure_ascii=False)
                            self.mqtt_client.publish(mqtt_topic, command_json)
                            print(f"명령 전달 완료: AGV {agv_id}")
                        else:
                            print("MQTT 연결 없음")
                    else:
                        print("필수 필드 누락")
                        
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 오류: {e}")
                except Exception as e:
                    print(f"명령 수신 오류: {e}")
                    self.connected_to_server = False
                    break
                    
        except Exception as e:
            print(f"수신 스레드 오류: {e}")
        
        self.connected_to_server = False
    
    def print_agv_status_summary(self):
        """AGV 상태 요약 출력 (주기적)"""
        if not self.agv_sensing_data:
            return
            
        print("\n=== AGV 상태 요약 ===")
        for agv_id, data in self.agv_sensing_data.items():
            last_update = data['last_update'].strftime("%H:%M:%S") if data['last_update'] else "없음"
            status_icon = "🔄" if data['work_status'] == 'working' else "🏁" if data['work_status'] == 'finished' else "⏸️"
            print(f"AGV {agv_id}: {status_icon} {data['work_status']} (마지막 업데이트: {last_update})")
        print("==================\n")
    
    def run(self):
        """메인 실행 루프"""
        self.running = True
        
        # MQTT 설정
        if not self.setup_mqtt():
            print("MQTT 설정 실패")
            return
        
        # 상태 요약 출력을 위한 카운터
        status_counter = 0
        
        try:
            while self.running:
                # 서버 연결 시도
                if not self.connected_to_server:
                    print("서버 연결 시도 중...")
                    if not self.connect_to_server():
                        print("서버 연결 실패, 5초 후 재시도")
                        time.sleep(5)
                        continue
                
                # 명령 수신 루프
                self.receive_server_commands()
                
                # 연결 끊어진 경우 재시도
                if not self.connected_to_server:
                    print("서버 연결 끊어짐, 5초 후 재연결")
                    time.sleep(5)
                
                # 주기적으로 AGV 상태 요약 출력 (30초마다)
                status_counter += 1
                if status_counter >= 6:  # 5초 * 6 = 30초
                    self.print_agv_status_summary()
                    status_counter = 0
        
        except KeyboardInterrupt:
            print("프로그램 종료 요청")
        finally:
            self.running = False
            if self.socket:
                self.socket.close()
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            print("프로그램 종료")


if __name__ == "__main__":
    bridge = RaspberryPiBridge()
    bridge.run()