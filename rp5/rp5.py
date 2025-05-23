import socket
import json
import time
import paho.mqtt.client as mqtt

# 서버 연결 설정
SERVER_HOST = '43.200.169.7'
SERVER_PORT = 5000
BUFFER_SIZE = 4096

# MQTT 설정
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

class RaspberryPiBridge:
    def __init__(self):
        self.socket = None
        self.mqtt_client = None
        self.connected_to_server = False
        self.connected_to_mqtt = False
        self.running = False
        
        print("라즈베리파이 브릿지 초기화")
    
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
            ident_data = {"client_type": "raspberry_pi"}
            data_string = json.dumps(ident_data)
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
            
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 30)
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
        else:
            print(f"MQTT 브로커 연결 실패: {rc}")
            self.connected_to_mqtt = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT 연결 해제 콜백"""
        print("MQTT 브로커 연결 해제됨")
        self.connected_to_mqtt = False
    
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
                    if "agv_id" in command and "start" in command and "end" in command and "delays" in command:
                        agv_id = command["agv_id"]
                        
                        # MQTT를 통해 AGV에 명령 전달
                        if self.connected_to_mqtt:
                            mqtt_topic = f"agv/{agv_id}/command"
                            self.mqtt_client.publish(mqtt_topic, command_string)
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
    
    def run(self):
        """메인 실행 루프"""
        self.running = True
        
        # MQTT 설정
        if not self.setup_mqtt():
            print("MQTT 설정 실패")
            return
        
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