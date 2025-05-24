import paho.mqtt.client as mqtt
import json
import time
import base64
import os
import threading
from datetime import datetime

# 외부 MQTT 브로커 설정 (별도 브로커 서버 필요)
MQTT_BROKER_HOST = "mqtt.broker.address"  # 실제 브로커 주소로 변경
MQTT_BROKER_PORT = 1883
MQTT_USERNAME = "raspberry_pi"
MQTT_PASSWORD = "AgvRaspberry2025!"

# 라즈베리파이 식별 정보
RASPBERRY_PI_ID = "rpi_001"  # 각 라즈베리파이마다 고유 ID 설정

# MQTT 토픽
COMMAND_TOPIC = f"server/commands/{RASPBERRY_PI_ID}"
STATUS_TOPIC = f"raspberrypi/status/{RASPBERRY_PI_ID}"
HEARTBEAT_TOPIC = "raspberrypi/heartbeat"

# 로컬 MQTT 브로커 설정 (AGV와 통신)
LOCAL_MQTT_BROKER = "localhost"
LOCAL_MQTT_PORT = 1883

# 이미지 저장 경로
IMAGE_SAVE_PATH = "/home/doit/ld/agv_images"

class RaspberryPiBridge:
    def __init__(self):
        # 중앙 서버와 통신용 MQTT 클라이언트
        self.server_mqtt_client = None
        self.connected_to_server = False
        
        # AGV와 통신용 로컬 MQTT 클라이언트
        self.local_mqtt_client = None
        self.connected_to_local_mqtt = False
        
        self.running = False
        
        # AGV별 센싱 데이터 저장
        self.agv_sensing_data = {}
        
        # 이미지 저장 디렉토리 생성
        self.ensure_image_directory()
        
        print(f"라즈베리파이 브릿지 초기화 - ID: {RASPBERRY_PI_ID}")
    
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
    
    def setup_server_mqtt(self):
        """중앙 서버와 통신용 MQTT 클라이언트 설정"""
        try:
            self.server_mqtt_client = mqtt.Client(client_id=f"{RASPBERRY_PI_ID}_server")
            self.server_mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
            self.server_mqtt_client.on_connect = self.on_server_mqtt_connect
            self.server_mqtt_client.on_disconnect = self.on_server_mqtt_disconnect
            self.server_mqtt_client.on_message = self.on_server_mqtt_message
            
            self.server_mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.server_mqtt_client.loop_start()
            
            return True
        except Exception as e:
            print(f"서버 MQTT 설정 오류: {e}")
            return False
    
    def setup_local_mqtt(self):
        """AGV와 통신용 로컬 MQTT 클라이언트 설정"""
        try:
            self.local_mqtt_client = mqtt.Client(client_id=f"{RASPBERRY_PI_ID}_local")
            
            self.local_mqtt_client.on_connect = self.on_local_mqtt_connect
            self.local_mqtt_client.on_disconnect = self.on_local_mqtt_disconnect
            self.local_mqtt_client.on_message = self.on_local_mqtt_message
            
            self.local_mqtt_client.connect(LOCAL_MQTT_BROKER, LOCAL_MQTT_PORT, 60)
            self.local_mqtt_client.loop_start()
            
            return True
        except Exception as e:
            print(f"로컬 MQTT 설정 오류: {e}")
            return False
    
    def on_server_mqtt_connect(self, client, userdata, flags, rc):
        """중앙 서버 MQTT 연결 콜백"""
        if rc == 0:
            print("✅ 중앙 서버 MQTT 브로커 연결 성공")
            self.connected_to_server = True
            
            # 명령 토픽 구독
            client.subscribe(COMMAND_TOPIC, 1)
            print(f"📡 명령 토픽 구독: {COMMAND_TOPIC}")
            
            # 하트비트 전송 시작
            self.start_heartbeat()
            
        else:
            print(f"❌ 중앙 서버 MQTT 브로커 연결 실패: {rc}")
            self.connected_to_server = False
    
    def on_server_mqtt_disconnect(self, client, userdata, rc):
        """중앙 서버 MQTT 연결 해제 콜백"""
        print("❌ 중앙 서버 MQTT 브로커 연결 해제됨")
        self.connected_to_server = False
    
    def on_server_mqtt_message(self, client, userdata, msg):
        """중앙 서버로부터 명령 수신 콜백"""
        try:
            command_string = msg.payload.decode('utf-8')
            command = json.loads(command_string)
            print(f"📥 중앙 서버로부터 명령 수신: {command}")
            
            # AGV로 명령 전달
            self.forward_command_to_agv(command)
            
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
        except Exception as e:
            print(f"명령 수신 오류: {e}")
    
    def on_local_mqtt_connect(self, client, userdata, flags, rc):
        """로컬 MQTT 연결 콜백"""
        if rc == 0:
            print("✅ 로컬 MQTT 브로커 연결 성공")
            self.connected_to_local_mqtt = True
            
            # AGV 센싱 토픽 구독 (AGV 1-4)
            for agv_id in range(1, 5):
                sensing_topic = f"agv/{agv_id}/sensing"
                client.subscribe(sensing_topic, 1)
                print(f"📡 AGV {agv_id} 센싱 토픽 구독: {sensing_topic}")
                
        else:
            print(f"❌ 로컬 MQTT 브로커 연결 실패: {rc}")
            self.connected_to_local_mqtt = False
    
    def on_local_mqtt_disconnect(self, client, userdata, rc):
        """로컬 MQTT 연결 해제 콜백"""
        print("❌ 로컬 MQTT 브로커 연결 해제됨")
        self.connected_to_local_mqtt = False
    
    def on_local_mqtt_message(self, client, userdata, msg):
        """AGV로부터 센싱 데이터 수신 콜백 - 새로운 JSON 포맷"""
        try:
            topic = msg.topic
            message = msg.payload.decode('utf-8')
            
            # 토픽에서 AGV ID 추출 (agv/{agv_id}/sensing)
            topic_parts = topic.split('/')
            if len(topic_parts) >= 3 and topic_parts[0] == 'agv' and topic_parts[2] == 'sensing':
                agv_id = str(topic_parts[1])  # 문자열로 통일
                
                # JSON 데이터 파싱
                sensing_data = json.loads(message)
                
                # 새로운 포맷 필드 확인
                work_id = sensing_data.get('workId')
                cmd_string = sensing_data.get('cmd_string')
                is_finished = sensing_data.get('is_finished', 0)
                
                print(f"AGV {agv_id} 센싱 데이터 수신: workId={work_id}, cmd_string={cmd_string}, is_finished={is_finished}")
                
                # 센싱 데이터 처리
                self.process_sensing_data(agv_id, sensing_data)
                
        except json.JSONDecodeError as e:
            print(f"센싱 데이터 JSON 파싱 오류: {e}")
        except Exception as e:
            print(f"센싱 데이터 처리 오류: {e}")
    
    def forward_command_to_agv(self, command):
        """중앙 서버로부터 받은 명령을 AGV로 전달"""
        try:
            agv_id = str(command["agv_id"])
            
            if self.connected_to_local_mqtt:
                mqtt_topic = f"agv/{agv_id}/command"
                
                # 명령 데이터 재구성
                agv_command = {
                    "agv_id": agv_id,
                    "start": command["start"],
                    "end": command["end"],
                    "delays": int(command["delays"]),
                    "item_idx": int(command["item_idx"]),
                    "timedata": command.get("timedata", datetime.now().isoformat())
                }
                
                command_json = json.dumps(agv_command, ensure_ascii=False)
                self.local_mqtt_client.publish(mqtt_topic, command_json)
                print(f"✅ 명령 전달 완료: AGV {agv_id} (물건 인덱스: {command['item_idx']})")
            else:
                print("❌ 로컬 MQTT 연결 없음")
                
        except Exception as e:
            print(f"명령 전달 오류: {e}")
    
    def process_sensing_data(self, agv_id, sensing_data):
        """AGV 센싱 데이터 처리 - 새로운 JSON 포맷"""
        try:
            # 새로운 포맷 필드 추출
            work_id = sensing_data.get('workId')
            cmd_string = sensing_data.get('cmd_string')
            is_finished = sensing_data.get('is_finished', 0)
            image_b64 = sensing_data.get('image')
            box_idx = sensing_data.get('box_idx', 0)
            time_str = sensing_data.get('time')
            
            # 현재 시간
            current_time = datetime.now()
            
            # AGV별 센싱 데이터 초기화
            if agv_id not in self.agv_sensing_data:
                self.agv_sensing_data[agv_id] = {
                    'last_update': None,
                    'work_status': 'idle',
                    'current_work_id': None,
                    'collision_count': 0,
                    'start_time': None,
                    'end_time': None
                }
            
            agv_data = self.agv_sensing_data[agv_id]
            
            # 이미지가 있는 경우 저장
            if image_b64:
                self.save_agv_image(agv_id, image_b64, cmd_string, current_time, work_id)
            
            # cmd_string에 따른 작업 상태 처리
            if cmd_string == "start":
                print(f"🚀 AGV {agv_id} 작업 시작! Work ID: {work_id}")
                agv_data['work_status'] = 'working'
                agv_data['current_work_id'] = work_id
                agv_data['start_time'] = current_time
                agv_data['collision_count'] = 0
                
                # 작업 시작 로그
                self.log_work_event(agv_id, "work_start", current_time, work_id, box_idx)
                
            elif cmd_string == "col":
                print(f"💥 AGV {agv_id} 충돌 발생! Work ID: {work_id}")
                agv_data['collision_count'] += 1
                
                # 충돌 로그
                self.log_work_event(agv_id, "collision", current_time, work_id, box_idx)
                
            elif cmd_string == "end":
                print(f"🏁 AGV {agv_id} 작업 완료! Work ID: {work_id}")
                agv_data['work_status'] = 'finished'
                agv_data['end_time'] = current_time
                
                # 작업 완료 로그
                self.log_work_event(agv_id, "work_complete", current_time, work_id, box_idx)
                
            elif cmd_string is None and agv_data['work_status'] == 'finished':
                # 작업 완료 후 대기 상태로 복귀
                print(f"⏸️ AGV {agv_id} 대기 상태로 복귀")
                agv_data['work_status'] = 'idle'
                agv_data['current_work_id'] = None
                agv_data['start_time'] = None
                agv_data['end_time'] = None
            
            # 마지막 업데이트 시간 갱신
            agv_data['last_update'] = current_time
            
            # 중앙 서버로 상태 정보 전송
            self.send_status_to_server(agv_id, agv_data, sensing_data)
            
        except Exception as e:
            print(f"센싱 데이터 처리 중 오류: {e}")
    
    def save_agv_image(self, agv_id, image_b64, cmd_string, timestamp, work_id):
        """AGV 이미지 저장 - 새로운 포맷"""
        try:
            # Base64 디코딩
            image_data = base64.b64decode(image_b64)
            
            # 파일명 생성
            time_str = timestamp.strftime("%Y%m%d_%H%M%S")
            status = cmd_string if cmd_string else "work"
            filename = f"agv_{agv_id}_{status}_{work_id}_{time_str}.jpg"
            
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
    
    def log_work_event(self, agv_id, event_type, timestamp, work_id, box_idx):
        """작업 이벤트 로그"""
        log_entry = {
            "agv_id": str(agv_id),
            "event": event_type,
            "timestamp": timestamp.isoformat(),
            "work_id": work_id,
            "box_idx": box_idx
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
    
    def send_status_to_server(self, agv_id, agv_data, original_sensing_data):
        """AGV 상태를 중앙 서버로 전송 - 새로운 포맷"""
        try:
            if not self.connected_to_server:
                return
            
            status_data = {
                "raspberry_pi_id": RASPBERRY_PI_ID,
                "agv_id": str(agv_id),
                "status": agv_data['work_status'],
                "work_id": agv_data.get('current_work_id'),
                "collision_count": agv_data.get('collision_count', 0),
                "cmd_string": original_sensing_data.get('cmd_string'),
                "is_finished": original_sensing_data.get('is_finished', 0),
                "box_idx": original_sensing_data.get('box_idx', 0),
                "timestamp": agv_data['last_update'].isoformat() if agv_data['last_update'] else None
            }
            
            data_string = json.dumps(status_data, ensure_ascii=False)
            self.server_mqtt_client.publish(STATUS_TOPIC, data_string, 1)
            print(f"📊 AGV {agv_id} 상태 정보 중앙 서버 전송")
            
        except Exception as e:
            print(f"서버 상태 전송 오류: {e}")
    
    def start_heartbeat(self):
        """하트비트 전송 시작"""
        def heartbeat_loop():
            while self.running and self.connected_to_server:
                try:
                    heartbeat_data = {
                        "raspberry_pi_id": RASPBERRY_PI_ID,
                        "timestamp": datetime.now().isoformat(),
                        "status": "online"
                    }
                    
                    data_string = json.dumps(heartbeat_data, ensure_ascii=False)
                    self.server_mqtt_client.publish(HEARTBEAT_TOPIC, data_string, 1)
                    print(f"💓 하트비트 전송: {RASPBERRY_PI_ID}")
                    
                except Exception as e:
                    print(f"하트비트 전송 오류: {e}")
                
                time.sleep(30)  # 30초마다 하트비트 전송
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
    
    def print_agv_status_summary(self):
        """AGV 상태 요약 출력 (주기적)"""
        if not self.agv_sensing_data:
            return
            
        print("\n=== AGV 상태 요약 ===")
        for agv_id, data in self.agv_sensing_data.items():
            last_update = data['last_update'].strftime("%H:%M:%S") if data['last_update'] else "없음"
            status_icon = "🔄" if data['work_status'] == 'working' else "🏁" if data['work_status'] == 'finished' else "⏸️"
            work_id = data.get('current_work_id', 'N/A')
            collision_count = data.get('collision_count', 0)
            print(f"AGV {agv_id}: {status_icon} {data['work_status']} | Work ID: {work_id} | 충돌: {collision_count}회 | 업데이트: {last_update}")
        print("==================\n")
    
    def run(self):
        """메인 실행 루프"""
        self.running = True
        
        # 중앙 서버 MQTT 설정
        if not self.setup_server_mqtt():
            print("❌ 중앙 서버 MQTT 설정 실패")
            return
        
        # 로컬 MQTT 설정
        if not self.setup_local_mqtt():
            print("❌ 로컬 MQTT 설정 실패")
            return
        
        # 연결 대기
        print("⏳ MQTT 연결 대기 중...")
        time.sleep(3)
        
        # 상태 요약 출력을 위한 카운터
        status_counter = 0
        
        try:
            while self.running:
                # 연결 상태 확인
                if not self.connected_to_server:
                    print("⚠️ 중앙 서버 연결이 끊어졌습니다. 재연결 시도 중...")
                    self.setup_server_mqtt()
                
                if not self.connected_to_local_mqtt:
                    print("⚠️ 로컬 MQTT 연결이 끊어졌습니다. 재연결 시도 중...")
                    self.setup_local_mqtt()
                
                # 주기적으로 AGV 상태 요약 출력 (30초마다)
                status_counter += 1
                if status_counter >= 6:  # 5초 * 6 = 30초
                    self.print_agv_status_summary()
                    status_counter = 0
                
                time.sleep(5)
        
        except KeyboardInterrupt:
            print("프로그램 종료 요청")
        finally:
            self.running = False
            if self.server_mqtt_client:
                self.server_mqtt_client.loop_stop()
                self.server_mqtt_client.disconnect()
            if self.local_mqtt_client:
                self.local_mqtt_client.loop_stop()
                self.local_mqtt_client.disconnect()
            print("프로그램 종료")


if __name__ == "__main__":
    bridge = RaspberryPiBridge()
    bridge.run()