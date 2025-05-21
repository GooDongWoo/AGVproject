import socket
import json
import time
import threading
import paho.mqtt.client as mqtt
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('RaspberryPi_Bridge')

# 서버 연결 설정
SERVER_HOST = '43.200.169.7'  # 또는 서버의 IP 주소
SERVER_PORT = 5000
BUFFER_SIZE = 4096

# MQTT 설정
MQTT_BROKER = "localhost"  # MQTT 브로커 주소
MQTT_PORT = 1883

class RaspberryPiBridge:
    def __init__(self, server_host=SERVER_HOST, server_port=SERVER_PORT,
                 mqtt_broker=MQTT_BROKER, mqtt_port=MQTT_PORT):
        """라즈베리 파이 브릿지 초기화"""
        self.server_host = server_host
        self.server_port = server_port
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.socket = None
        self.mqtt_client = None
        self.connected_to_server = False
        self.connected_to_mqtt = False
        self.running = False
        
        logger.info(f"브릿지 초기화: 서버={server_host}:{server_port}, MQTT={mqtt_broker}:{mqtt_port}")
    
    def connect_to_server(self):
        """서버에 소켓 연결"""
        logger.info(f"서버 {self.server_host}:{self.server_port}에 연결 시도")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.server_host, self.server_port))
            self.socket.settimeout(None)
            self.connected_to_server = True
            logger.info("서버 연결 성공")
            
            # 연결 후 라즈베리 파이로 식별
            self.send_identification()
            return True
        except Exception as e:
            logger.error(f"서버 연결 오류: {e}")
            self.connected_to_server = False
            return False
    
    def send_identification(self):
        """서버에 라즈베리 파이 식별 정보 전송"""
        try:
            ident_data = {
                "client_type": "raspberry_pi"
            }
            data_string = json.dumps(ident_data)
            self.socket.sendall(data_string.encode('utf-8'))
            logger.info("식별 정보 전송 완료")
            return True
        except Exception as e:
            logger.error(f"식별 정보 전송 오류: {e}")
            self.connected_to_server = False
            return False
    
    def setup_mqtt(self):
        """MQTT 클라이언트 설정"""
        try:
            client_id = f"raspberry_pi_bridge"
            self.mqtt_client = mqtt.Client(client_id=client_id)
            
            # 콜백 함수 설정
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            # MQTT 브로커에 연결
            logger.info(f"MQTT 브로커 {self.mqtt_broker}:{self.mqtt_port}에 연결 시도")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            
            # 백그라운드에서 MQTT 루프 시작
            self.mqtt_client.loop_start()
            
            return True
        except Exception as e:
            logger.error(f"MQTT 설정 오류: {e}")
            return False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT 연결 콜백"""
        if rc == 0:
            logger.info("MQTT 브로커 연결 성공")
            self.connected_to_mqtt = True
        else:
            logger.error(f"MQTT 브로커 연결 실패, 코드: {rc}")
            self.connected_to_mqtt = False
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT 연결 해제 콜백"""
        logger.warning("MQTT 브로커 연결 해제됨")
        self.connected_to_mqtt = False
    
    def disconnect_server(self):
        """서버 연결 해제"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("서버 연결 해제 완료")
            except Exception as e:
                logger.error(f"서버 연결 해제 오류: {e}")
        self.connected_to_server = False
    
    def disconnect_mqtt(self):
        """MQTT 연결 해제"""
        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("MQTT 연결 해제 완료")
            except Exception as e:
                logger.error(f"MQTT 연결 해제 오류: {e}")
        self.connected_to_mqtt = False
    
    def receive_server_commands(self):
        """서버로부터 명령 수신 및 AGV로 전달"""
        if not self.connected_to_server:
            logger.warning("서버에 연결되어 있지 않습니다")
            return
        
        try:
            while self.running:
                try:
                    # 서버로부터 데이터 수신
                    data = self.socket.recv(BUFFER_SIZE)
                    
                    if not data:
                        logger.warning("서버 연결 종료 (빈 데이터)")
                        self.connected_to_server = False
                        break
                    
                    # 데이터 처리
                    command_string = data.decode('utf-8')
                    try:
                        command = json.loads(command_string)
                        logger.info(f"서버로부터 명령 수신: {command}")
                        
                        # 필수 필드 확인
                        if "agv_id" in command and "start_flag" in command and "start_location" in command and "destination" in command and "delay_seconds" in command:
                            agv_id = command["agv_id"]
                            
                            # MQTT를 통해 AGV에 명령 전달
                            if self.connected_to_mqtt:
                                mqtt_topic = f"agv/{agv_id}/command"
                                self.mqtt_client.publish(mqtt_topic, command_string)
                                logger.info(f"명령 전달 완료: AGV {agv_id}")
                            else:
                                logger.warning("MQTT 연결 없음, 명령 전달 실패")
                        else:
                            logger.warning(f"누락된 필드가 있는 명령: {command}")
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON 파싱 오류: {e}")
                
                except ConnectionResetError:
                    logger.error("서버 연결 재설정됨")
                    self.connected_to_server = False
                    break
                except Exception as e:
                    logger.error(f"명령 수신 오류: {e}")
                    self.connected_to_server = False
                    break
            
            logger.info("명령 수신 루프 종료")
            
        except Exception as e:
            logger.error(f"수신 스레드 오류: {e}")
        
        self.connected_to_server = False
    
    def run(self):
        """메인 실행 루프"""
        self.running = True
        
        # MQTT 설정
        if not self.setup_mqtt():
            logger.error("MQTT 설정 실패")
            return
        
        try:
            while self.running:
                # 연결 상태 확인
                if not self.connected_to_server:
                    logger.info("서버 연결 시도 중...")
                    if not self.connect_to_server():
                        logger.warning("서버 연결 실패, 5초 후 재시도")
                        time.sleep(5)
                        continue
                
                # 명령 수신 루프 시작
                self.receive_server_commands()
                
                # 연결 끊어진 경우 재시도
                if not self.connected_to_server:
                    logger.info("서버 연결이 끊어짐, 5초 후 재연결")
                    time.sleep(5)
        
        except KeyboardInterrupt:
            logger.info("프로그램 종료 요청")
        finally:
            self.running = False
            self.disconnect_server()
            self.disconnect_mqtt()
            logger.info("프로그램 종료")


if __name__ == "__main__":
    logger.info("라즈베리 파이 브릿지 시작")
    bridge = RaspberryPiBridge()
    bridge.run()