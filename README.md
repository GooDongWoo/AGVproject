# AGV 자율주행 시스템

## 📋 프로젝트 개요

AGV(Autonomous Guided Vehicle) 자율주행 시스템은 JetBot 기반의 로봇이 AI 모델을 활용하여 라인을 따라 이동하며, 색상 인식을 통해 지정된 작업 영역에서 물건을 집고 배송하는 자동화 시스템입니다.

## 🏗️ 시스템 아키텍처

```
중앙 서버 (EC2) ←→ 라즈베리파이 (브릿지) ←→ AGV (JetBot)
    │                    │                      │
    │                    │                      ├─ AI 모델 (라인 추종)
    │                    │                      ├─ 컴퓨터 비전 (색상 인식)
    │                    │                      └─ 하드웨어 제어
    │                    │
    │                    ├─ MQTT 브로커
    │                    ├─ Firebase 연동
    │                    └─ OpenAI 연동
    │
    └─ 명령 전송 및 모니터링
```

## 🎯 주요 기능

### 1. AGV 자율주행
- **AI 기반 라인 추종**: ResNet18 모델을 사용한 실시간 경로 인식
- **색상 기반 작업 영역 인식**: 6가지 색상(빨강, 초록, 파랑, 보라, 노랑, 주황) 구분
- **자동 집/배송**: 지정된 영역에서 물건 자동 집기/놓기
- **실시간 센서 데이터 전송**: 0.5초 주기로 상태 정보 전송

### 2. 통신 시스템
- **MQTT 프로토콜**: 실시간 양방향 통신
- **JSON 데이터 포맷**: 구조화된 명령 및 센서 데이터
- **소켓 통신**: 중앙 서버와 라즈베리파이 간 안정적 연결

### 3. 중앙 관리
- **작업 명령 전송**: 웹 기반 명령 인터페이스
- **실시간 모니터링**: AGV 상태 및 작업 진행도 추적
- **멀티 AGV 관리**: 여러 AGV 동시 제어 및 조율

## 📁 프로젝트 구조

```
agv-system/
├── server/
│   ├── server.cpp              # 중앙 서버 (C++)
│   └── Makefile               # 빌드 설정
├── raspberry-pi/
│   └── rp5.py                 # 라즈베리파이 브릿지
├── agv/
│   ├── main.ipynb             # AGV 메인 시스템
│   ├── config.py              # 설정 파일
│   ├── mqtt_manager.py        # MQTT 통신 관리
│   ├── road_following.py      # 라인 추종 모듈
│   └── area_detecting.py      # 영역 인식 모듈
└── README.md
```

## 🚀 시작하기

### 1. 중앙 서버 설정

```bash
# 의존성 설치 (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install g++ libnlohmann-json3-dev

# 컴파일
cd server/
g++ -std=c++17 -pthread -o server server.cpp

# 실행
./server
```

### 2. 라즈베리파이 설정

```bash
# Python 의존성 설치
pip install paho-mqtt socket json

# 브릿지 실행
cd raspberry-pi/
python3 rp5.py
```

### 3. AGV (JetBot) 설정

```bash
# JetBot 환경에서 실행
# Jupyter Notebook 또는 직접 Python 실행
cd agv/
python3 -c "exec(open('main.ipynb').read())"
```

## ⚙️ 설정

### AGV 설정 (config.py)

```python
# AGV 식별
AGV_ID = "AGV_1"  # 각 AGV마다 고유 ID

# MQTT 브로커
MQTT_BROKER_ADDRESS = "192.168.0.22"
MQTT_BROKER_PORT = 1883

# 색상 인식 임계값
ARRIVAL_THRESHOLD_X = 15
ARRIVAL_THRESHOLD_Y = 15

# 모터 제어 파라미터
SPEED_GAIN = 0.17
STEERING_GAIN = 0.2
```

### 중앙 서버 설정

```cpp
// 서버 포트 및 연결 설정
const int PORT = 5000;
const int MAX_CONNECTIONS = 5;

// 지원 색상
const std::vector<std::string> COLOR_LIST = {
    "red", "green", "blue", "purple", "yellow", "orange"
};
```

## 📊 데이터 포맷

### 작업 명령 (서버 → AGV)

```json
{
    "timedata": "2025-05-22 14:30:15",
    "start": 0,        // 시작 색상 인덱스 (또는 "red")
    "end": 2,          // 끝 색상 인덱스 (또는 "blue")
    "delays": 5,       // 지연 시간 (초)
    "agv_id": "AGV_1"
}
```

### 센서 데이터 (AGV → 서버)

```json
{
    "is_finished": 0,           // 작업 완료 여부 (0/1)
    "bgr_image": "base64..."    // 카메라 이미지 (Base64)
}
```

## 🎮 사용법

### 중앙 서버 명령어

```bash
AGV> help        # 도움말 보기
AGV> list        # 연결된 라즈베리파이 목록
AGV> send        # 대화형 명령 전송
AGV> quick       # 빠른 명령 전송
AGV> colors      # 사용 가능한 색상 목록
AGV> exit        # 서버 종료
```

### 빠른 명령 예시

```bash
# 형식: <라즈베리파이번호> <AGV_ID> <시작색상> <끝색상> <지연시간>
AGV> quick
입력: 1 AGV_1 red blue 5
```

## 🔄 AGV 작업 흐름

### 1. 시스템 초기화
```
AGV 부팅 → 하드웨어 초기화 → AI 모델 로드 → MQTT 연결 → 명령 대기
```

### 2. 작업 수행 과정
```
① 라즈베리파이로부터 작업 명령 수신
   └─ 시작장소, 끝장소, 지연시간, 작업ID 포함

② 지연시간 후 자동 모드 시작
   └─ Thread 1: 라인 팔로잉 시작
   └─ Thread 2: 첫 번째 목표 영역(집하장소) 탐색

③ 첫 번째 영역 도착 감지
   └─ 중심점 좌표가 임계값 이내 진입
   └─ 자동 집기 동작 수행 (서보 제어)
   └─ 목표 전환: 집하장소 → 배송장소

④ 두 번째 목표 영역(배송장소) 탐색
   └─ 계속된 라인 팔로잉 + 영역 탐지

⑤ 두 번째 영역 도착 및 배송
   └─ 자동 놓기 동작 수행
   └─ 작업 완료 상태로 전환

⑥ 작업 완료 보고
   └─ 상태 정보 라즈베리파이로 전송
   └─ 대기 상태로 복귀
```

## 🧠 AI 및 제어 알고리즘

### 라인 추종 (Road Following)
- **입력**: 224x224 카메라 영상
- **모델**: ResNet18 기반 회귀 모델
- **출력**: x, y 좌표 (주행 방향)
- **제어**: PID 제어기를 통한 조향각 계산

```python
# PID 제어 공식
angle = arctan2(x, y)
pid = angle * STEERING_GAIN + (angle - angle_last) * STEERING_DGAIN
steering = pid + STEERING_BIAS
```

### 색상 영역 인식 (Area Detection)
- **색상 공간**: HSV 변환
- **전처리**: 블러링 → 마스킹 → 침식/팽창
- **윤곽선 검출**: OpenCV contour detection
- **도착 판정**: 중심점 거리 기반 임계값 검사

## 🔧 주요 기술 스택

### 하드웨어
- **JetBot**: NVIDIA Jetson Nano 기반 로봇 플랫폼
- **카메라**: CSI 카메라 (224x224 해상도)
- **모터**: 차동 조향 시스템
- **서보**: 물건 집기/놓기 메커니즘

### 소프트웨어
- **AI 모델**: PyTorch, ResNet18
- **컴퓨터 비전**: OpenCV, PIL
- **통신**: MQTT (Paho), Socket Programming
- **언어**: Python 3.x, C++17
- **플랫폼**: Linux (Ubuntu/Jetson), Raspberry Pi OS

## 📈 성능 특징

- **실시간 처리**: 100ms 주기 제어 루프
- **고정밀 인식**: ±15픽셀 도착 판정 정확도
- **안정적 통신**: QoS Level 1 MQTT 통신
- **병렬 처리**: 멀티스레딩으로 동시 작업 수행
- **확장성**: 모듈화된 구조로 쉬운 기능 추가

## 🛠️ 문제 해결

### 일반적인 문제

#### 1. MQTT 연결 실패
```bash
# 브로커 주소 및 포트 확인
ping <MQTT_BROKER_ADDRESS>
telnet <MQTT_BROKER_ADDRESS> 1883

# 방화벽 설정 확인
sudo ufw status
sudo ufw allow 1883
```

#### 2. AI 모델 로드 오류
```python
# 모델 파일 경로 확인
import os
print(os.path.exists("best.pth"))

# CUDA 사용 가능 여부 확인
import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"CUDA Version: {torch.version.cuda}")
```

#### 3. 색상 인식 불량
```python
# HSV 범위 디버깅
import cv2
import numpy as np

# 실시간 HSV 값 확인
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv_value = hsv[y, x]
        print(f"HSV at ({x}, {y}): {hsv_value}")

cv2.setMouseCallback('frame', mouse_callback)
```

#### 4. 네트워크 연결 문제
```bash
# 네트워크 인터페이스 확인
ifconfig

# 라즈베리파이와 AGV 간 연결 테스트
ping <RASPBERRY_PI_IP>
```

## 📊 모니터링 및 디버깅

### 로그 파일 위치
```bash
# AGV 로그
/var/log/agv/system.log

# MQTT 로그  
/var/log/mosquitto/mosquitto.log

# 중앙 서버 로그
./server.log
```

### 실시간 상태 확인
```bash
# MQTT 메시지 모니터링
mosquitto_sub -h localhost -t "agv/+/sensing"

# 시스템 리소스 확인
htop
nvidia-smi  # Jetson에서
```

## 🔒 보안 고려사항

### MQTT 보안
```python
# TLS/SSL 설정 (권장)
client.tls_set(ca_certs=None, certfile=None, keyfile=None)
client.username_pw_set("username", "password")
```

### 네트워크 보안
```bash
# 방화벽 설정
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 1883  # MQTT
sudo ufw allow 5000  # 중앙 서버
```

## 🚀 배포 가이드

### Docker 배포 (선택사항)
```dockerfile
# Dockerfile for AGV
FROM nvcr.io/nvidia/l4t-pytorch:r32.6.1-pth1.9-py3

WORKDIR /app
COPY agv/ .
RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
```

### 시스템 서비스 등록
```bash
# systemd 서비스 생성
sudo nano /etc/systemd/system/agv.service

# 서비스 활성화
sudo systemctl enable agv.service
sudo systemctl start agv.service
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 개발 가이드라인
- 모든 코드는 PEP 8 스타일 가이드를 따릅니다
- 새로운 기능 추가 시 단위 테스트를 포함해주세요
- 문서화를 위해 docstring을 작성해주세요

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 연락처

프로젝트 관련 문의사항이 있으시면 언제든 연락주세요.

- **이메일**: [your-email@example.com]
- **GitHub**: [https://github.com/username/agv-system]
- **이슈 트래커**: [https://github.com/username/agv-system/issues]

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 프로젝트들의 도움을 받았습니다:

- [NVIDIA JetBot](https://github.com/NVIDIA-AI-IOT/jetbot) - JetBot 하드웨어 플랫폼
- [PyTorch](https://pytorch.org/) - 딥러닝 프레임워크
- [OpenCV](https://opencv.org/) - 컴퓨터 비전 라이브러리
- [Eclipse Paho MQTT](https://www.eclipse.org/paho/) - MQTT 클라이언트 라이브러리

## 📚 추가 자료

### 관련 문서
- [JetBot 설치 가이드](https://jetbot.org/master/software_setup/index.html)
- [PyTorch 모델 최적화](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)
- [MQTT 프로토콜 가이드](https://mqtt.org/mqtt-specification/)

### 튜토리얼 비디오
- AGV 시스템 설치 및 설정
- 라인 추종 모델 훈련 방법
- 색상 인식 파라미터 조정

---

## ⚠️ 주의사항

- **하드웨어 요구사항**: JetBot 하드웨어와 NVIDIA Jetson Nano가 필요합니다
- **환경 조건**: 충분한 조명 환경에서 최적의 성능을 발휘합니다
- **네트워크**: 안정적인 Wi-Fi 연결이 필요합니다
- **안전**: 테스트 시 충분한 공간을 확보하고 안전에 주의하세요

## 🏃‍♂️ 빠른 시작

처음 사용하시는 분들을 위한 단계별 가이드:

1. **하드웨어 준비** ✅
2. **소프트웨어 설치** ✅  
3. **네트워크 설정** ✅
4. **첫 번째 테스트 실행** ✅
5. **색상 영역 설정** ✅
6. **자율주행 테스트** ✅

각 단계별 자세한 내용은 [Wiki](링크)를 참조하세요.

---

**즐거운 AGV 개발 되세요! 🚗💨**