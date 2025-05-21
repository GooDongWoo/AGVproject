import socket
import json
import time
import random

# 서버 연결 설정
SERVER_HOST = '43.200.169.7'  # 또는 서버의 IP 주소
SERVER_PORT = 5000
BUFFER_SIZE = 4096

class AgvClient:
    def __init__(self, agv_id, server_host=SERVER_HOST, server_port=SERVER_PORT):
        """AGV 클라이언트 초기화"""
        self.agv_id = agv_id
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.connected = False
        self.running = False
        
        # AGV 초기 상태
        self.position = {'x': 0, 'y': 0}
        self.battery_level = 100
        self.status = "idle"  # idle, moving, charging 등
        self.load = None      # 현재 적재 중인 화물
        
        print(f"AgvClient 초기화 완료: ID={agv_id}, 서버={server_host}:{server_port}")
        
    def connect(self):
        """서버에 연결"""
        print(f"서버 {self.server_host}:{self.server_port}에 연결 시도 중...")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 연결 타임아웃 설정 (5초)
            self.socket.settimeout(5)
            self.socket.connect((self.server_host, self.server_port))
            self.socket.settimeout(None)  # 타임아웃 해제 (블로킹 모드)
            self.connected = True
            print(f"AGV {self.agv_id}가 서버에 성공적으로 연결되었습니다")
            return True
        except socket.timeout:
            print(f"연결 타임아웃: 서버 {self.server_host}:{self.server_port}가 응답하지 않습니다")
            self.connected = False
            return False
        except ConnectionRefusedError:
            print(f"연결 거부됨: 서버 {self.server_host}:{self.server_port}가 실행 중이 아닙니다")
            self.connected = False
            return False
        except Exception as e:
            print(f"연결 오류 발생: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """서버 연결 해제"""
        if self.socket:
            try:
                self.socket.close()
                print(f"소켓이 성공적으로 닫혔습니다")
            except Exception as e:
                print(f"소켓 닫기 오류: {e}")
        self.connected = False
        self.running = False
        print(f"AGV {self.agv_id}가 서버 연결을 해제했습니다")
    
    def generate_status(self):
        """현재 AGV 상태를 JSON 데이터로 생성"""
        # 실제 애플리케이션에서는 센서 데이터를 수집할 것입니다
        status_data = {
            "agv_id": self.agv_id,
            "position": self.position,
            "battery_level": self.battery_level,
            "status": self.status,
            "load": self.load,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return status_data
    
    def send_status(self):
        """현재 상태를 서버로 전송"""
        if not self.connected:
            print("서버에 연결되어 있지 않습니다")
            return False
        
        try:
            status_data = self.generate_status()
            data_string = json.dumps(status_data)
            self.socket.sendall(data_string.encode('utf-8'))
            print(f"상태 전송 완료: {data_string}")
            return True
        except ConnectionResetError:
            print("연결이 서버에 의해 재설정되었습니다")
            self.connected = False
            return False
        except BrokenPipeError:
            print("파이프가 끊어졌습니다 - 서버가 연결을 닫았습니다")
            self.connected = False
            return False
        except Exception as e:
            print(f"상태 전송 오류: {e}")
            self.connected = False
            return False
    
    def receive_command(self):
        """서버로부터 명령 수신 및 처리"""
        if not self.connected:
            print("서버에 연결되어 있지 않습니다")
            return None
        
        try:
            print("서버로부터 명령 대기 중...")
            # 소켓을 5초 타임아웃으로 설정
            self.socket.settimeout(5)
            data = self.socket.recv(BUFFER_SIZE)
            # 소켓을 다시 블로킹 모드로 설정
            self.socket.settimeout(None)
            
            if not data:
                print("서버가 연결을 종료했습니다 (빈 데이터 수신)")
                self.connected = False
                return None
            
            command_string = data.decode('utf-8')
            command = json.loads(command_string)
            print(f"명령 수신 완료: {command_string}")
            return command
        except socket.timeout:
            print("명령 수신 타임아웃 - 서버로부터 응답 없음")
            return None
        except ConnectionResetError:
            print("연결이 서버에 의해 재설정되었습니다")
            self.connected = False
            return None
        except json.JSONDecodeError as e:
            print(f"잘못된 JSON 데이터 수신: {e}")
            return None
        except Exception as e:
            print(f"명령 수신 오류: {e}")
            self.connected = False
            return None
    
    def process_command(self, command):
        """서버로부터 받은 명령 처리"""
        if not command:
            return
        
        try:
            # 명령 세부사항 추출
            command_id = command.get("command_id")
            action = command.get("action")
            parameters = command.get("parameters", {})
            
            print(f"명령 {command_id} 처리 중: {action}")
            
            # 다양한 명령 유형 처리
            if action == "move":
                # 이동 명령에 따라 위치 업데이트
                target_x = parameters.get("x")
                target_y = parameters.get("y")
                
                # 이동 시뮬레이션
                self.status = "moving"
                print(f"{self.position}에서 x:{target_x}, y:{target_y}로 이동 중")
                
                # 실제 구현에서는 실제 이동을 트리거할 것입니다
                # 시뮬레이션을 위해 위치만 업데이트합니다
                self.position = {'x': target_x, 'y': target_y}
                self.status = "idle"
                
                # 배터리 소모 시뮬레이션
                self.battery_level = max(0, self.battery_level - random.randint(1, 5))
                print(f"이동 완료. 현재 위치: {self.position}, 배터리: {self.battery_level}%")
            
            elif action == "charge":
                # 충전 시뮬레이션
                self.status = "charging"
                print(f"배터리 충전 중 {self.battery_level}%에서")
                
                # 충전 과정 시뮬레이션
                self.battery_level = min(100, self.battery_level + random.randint(10, 30))
                self.status = "idle"
                print(f"충전 완료. 배터리: {self.battery_level}%")
            
            elif action == "pickup":
                # 화물 픽업 시뮬레이션
                item_id = parameters.get("item_id")
                self.status = "loading"
                print(f"화물 픽업 중: {item_id}")
                
                # 적재 상태 업데이트
                self.load = item_id
                self.status = "idle"
                print(f"픽업 완료. 현재 적재 화물: {self.load}")
            
            elif action == "dropoff":
                # 화물 하차 시뮬레이션
                self.status = "unloading"
                print(f"화물 하차 중: {self.load}")
                
                # 적재 상태 업데이트
                self.load = None
                self.status = "idle"
                print(f"하차 완료. 현재 적재 화물: {self.load}")
            
            else:
                print(f"알 수 없는 명령: {action}")
            
        except Exception as e:
            print(f"명령 처리 오류: {e}")
    
    def run(self):
        """메인 동작 루프"""
        self.running = True
        
        # 서버에 연결
        if not self.connect():
            print("서버 연결 실패. 5초마다 재시도합니다.")
            
        try:
            while self.running:
                # 연결 상태 확인
                if not self.connected:
                    print("서버에 연결되어 있지 않습니다. 연결 시도 중...")
                    if not self.connect():
                        print("연결 실패, 5초 후 재시도...")
                        time.sleep(5)
                        continue
                
                # 연결된 경우에만 진행
                print("서버 연결 상태: 연결됨")
                
                # 현재 상태를 서버로 전송
                print("상태 전송 시도 중...")
                if not self.send_status():
                    print("상태 전송 실패, 재연결 시도 중...")
                    if not self.connect():
                        print("재연결 실패, 5초 후 재시도...")
                        time.sleep(5)
                        continue
                
                # 명령 수신 및 처리
                print("명령 대기 중...")
                command = self.receive_command()
                if command:
                    self.process_command(command)
                else:
                    print("유효한 명령을 받지 못했습니다.")
                    # 명령 수신에 실패한 경우 재연결 시도
                    if not self.connected:
                        print("연결이 끊어졌습니다, 재연결 중...")
                        if not self.connect():
                            print("재연결 실패, 5초 후 재시도...")
                            time.sleep(5)
                            continue
                
                # 다음 상태 업데이트 전 대기
                print(f"5초 대기 중...")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\nAGV 클라이언트 종료 중...")
        finally:
            self.disconnect()
            print("AGV 클라이언트가 중지되었습니다.")


def main():
    """단일 AGV 클라이언트를 실행하는 메인 함수"""
    print("프로그램 시작")
    
    # AGV ID 설정
    agv_id = "AGV_1"  # AGV ID를 원하는 대로 변경 가능
    
    print(f"AGV 클라이언트 ({agv_id}) 생성 중...")
    # AGV 클라이언트 생성
    agv = AgvClient(agv_id)
    
    print(f"{agv_id} 클라이언트를 시작합니다. 중지하려면 Ctrl+C를 누르세요.")
    
    # 메인 루프 실행
    agv.run()
    
    print("프로그램 종료")


if __name__ == "__main__":
    main()
