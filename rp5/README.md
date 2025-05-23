# 🍓 라즈베리파이 rp5.py 작동 흐름 가이드

## 📋 시스템 개요
라즈베리파이는 **중앙 서버**와 **AGV들** 사이의 **브릿지 역할**을 수행하며, 명령 전달과 센싱 데이터 수집을 담당합니다.

---

## 🚀 1. 시스템 초기화 단계

### `__init__(self)`
**역할**: 시스템 초기 설정 및 변수 초기화
```python
- 소켓 및 MQTT 클라이언트 변수 초기화
- 연결 상태 플래그 설정 (connected_to_server, connected_to_mqtt)
- AGV별 센싱 데이터 저장소 생성 (agv_sensing_data)
- 실행 상태 플래그 초기화 (running)
```

### `ensure_image_directory(self)`
**역할**: 이미지 저장을 위한 디렉토리 구조 생성
```python
- 메인 이미지 디렉토리 생성: /home/pi/agv_images/
- AGV별 서브디렉토리 생성: agv_1/, agv_2/, agv_3/, agv_4/
- 디렉토리 존재 여부 확인 후 필요시 생성
- 권한 오류 처리
```

---

## 🔗 2. 연결 설정 단계

### `setup_mqtt(self)`
**역할**: MQTT 브로커와의 연결 설정
```python
- MQTT 클라이언트 인스턴스 생성
- 콜백 함수 등록 (on_connect, on_disconnect, on_message)
- 브로커 연결 시도 (localhost:1883)
- 백그라운드 루프 시작
```

### `connect_to_server(self)`
**역할**: 중앙 서버와의 소켓 연결 설정
```python
- TCP 소켓 생성 및 서버 연결 (43.200.169.7:5000)
- 타임아웃 설정 (5초)
- 라즈베리파이 식별 데이터 전송 {"client_type": "raspberry_pi"}
- 연결 상태 플래그 업데이트
```

---

## 📡 3. MQTT 이벤트 처리

### `on_mqtt_connect(self, client, userdata, flags, rc)`
**역할**: MQTT 브로커 연결 성공 시 실행
```python
- 연결 상태 코드 확인 (rc == 0이면 성공)
- AGV 센싱 토픽 구독: agv/1/sensing, agv/2/sensing, agv/3/sensing, agv/4/sensing
- QoS Level 1로 구독 설정
- 연결 상태 플래그 업데이트
```

### `on_mqtt_message(self, client, userdata, msg)`
**역할**: AGV로부터 MQTT 메시지 수신 시 실행
```python
- 토픽 파싱하여 AGV ID 추출 (agv/{agv_id}/sensing)
- JSON 페이로드 디코딩
- process_sensing_data() 호출하여 센싱 데이터 처리
- 오류 처리 (JSON 파싱 오류, 토픽 형식 오류)
```

---

## 🎯 4. 센싱 데이터 처리 (핵심 로직)

### `process_sensing_data(self, agv_id, sensing_data)`
**역할**: AGV 센싱 데이터 분석 및 상태 업데이트
```python
📥 입력 데이터:
  - agv_id: AGV 식별자
  - sensing_data: {"is_finished": 0/1, "bgr_image": "base64_string"}

🔄 처리 흐름:
  1. AGV별 데이터 구조 초기화 (처음 수신 시)
  2. 이미지 데이터 저장 (save_agv_image 호출)
  3. 작업 상태 변화 감지:
     - is_finished == 1: 작업 완료 → log_work_completion() 호출
     - is_finished == 0 & 이전 상태가 idle: 작업 시작 → log_work_start() 호출
     - is_finished == 0 & 이전 상태가 finished: 대기 상태 복귀
  4. 마지막 업데이트 시간 갱신
  5. 서버로 상태 정보 전송 (send_agv_status_to_server 호출)
```

### `save_agv_image(self, agv_id, image_b64, is_finished, timestamp)`
**역할**: Base64 이미지를 파일로 저장
```python
📸 이미지 저장 과정:
  1. Base64 디코딩 → 바이너리 데이터 변환
  2. 파일명 생성: agv_{id}_{status}_{timestamp}.jpg
     - status: "work" (작업중) 또는 "end" (완료)
  3. AGV별 디렉토리에 JPG 파일 저장
  4. 파일 크기 확인 및 로그 출력
```

---

## 📝 5. 로깅 시스템

### `log_work_start(self, agv_id, timestamp)`
**역할**: 작업 시작 이벤트 로깅
```python
📋 로그 데이터:
  - agv_id: AGV 식별자
  - event: "work_start"
  - timestamp: ISO 형식 시간
  - work_id: 고유 작업 ID (agv_id + timestamp)
```

### `log_work_completion(self, agv_id, timestamp)`
**역할**: 작업 완료 이벤트 로깅
```python
📋 로그 데이터:
  - agv_id: AGV 식별자
  - event: "work_complete"
  - timestamp: ISO 형식 시간
  - work_id: 현재 작업 ID
```

### `write_log(self, log_entry)`
**역할**: 로그 데이터를 파일에 기록
```python
- 로그 파일: /home/pi/agv_images/agv_work_log.txt
- JSON 형태로 한 줄씩 추가 (append mode)
- UTF-8 인코딩으로 저장
```

---

## 🖥️ 6. 서버 통신

### `receive_server_commands(self)`
**역할**: 중앙 서버로부터 AGV 명령 수신 및 전달
```python
🔄 명령 처리 흐름:
  1. 서버 소켓에서 데이터 수신 (블로킹)
  2. JSON 형태 명령 파싱
  3. 필수 필드 검증: agv_id, start, end, delays
  4. MQTT를 통해 해당 AGV에 명령 전달
     - 토픽: agv/{agv_id}/command
  5. 전달 완료 로그 출력
```

### `send_agv_status_to_server(self, agv_id, agv_data, is_finished)`
**역할**: AGV 상태 정보를 서버로 전송 (선택적)
```python
📊 전송 데이터:
  - type: "agv_status"
  - agv_id: AGV 식별자
  - status: 현재 작업 상태 (idle/working/finished)
  - is_finished: 완료 플래그
  - last_update: 마지막 업데이트 시간
  - work_id: 현재 작업 ID
```

---

## 📊 7. 모니터링 시스템

### `print_agv_status_summary(self)`
**역할**: 전체 AGV 상태 요약 출력
```python
🖥️ 출력 형태:
=== AGV 상태 요약 ===
AGV 1: 🔄 working (마지막 업데이트: 14:32:15)
AGV 2: ⏸️ idle (마지막 업데이트: 14:30:22)
AGV 3: 🏁 finished (마지막 업데이트: 14:31:45)
AGV 4: ⏸️ idle (마지막 업데이트: 없음)
==================
```

---

## 🔄 8. 메인 실행 루프

### `run(self)`
**역할**: 시스템 전체 실행 흐름 제어
```python
🚀 실행 순서:
  1. running 플래그 True 설정
  2. MQTT 설정 및 연결 (setup_mqtt)
  3. 무한 루프 시작:
     a. 서버 연결 상태 확인
     b. 연결 안됨 → connect_to_server() 재시도
     c. 연결 됨 → receive_server_commands() 실행
     d. 연결 끊어짐 → 5초 대기 후 재연결
     e. 30초마다 AGV 상태 요약 출력
  4. 종료 시 리소스 정리 (소켓, MQTT 연결 해제)
```

---

## 📈 데이터 흐름도

```
[중앙 서버] ─────────────────────┐
    │                          │
    │ ① 작업 명령 전송              │ ⑤ AGV 상태 수신
    │ (JSON via Socket)         │ (JSON via Socket)
    │                          │
    ▼                          │
[라즈베리파이] ──────────────────────┘
    │ ② 명령 전달                 ▲ ④ 상태 정보 전송
    │ (MQTT)                    │ (가공된 데이터)
    ▼                          │
[AGV 1~4] ─────────────────────┘
      │ ③ 센싱 데이터 송신
      │ (MQTT: is_finished + 이미지)
      ▼
[라즈베리파이 저장소]
  ├── 이미지 파일 (.jpg)
  ├── 작업 로그 (.txt)
  └── 상태 데이터 (메모리)
```

---

## 🔧 시스템 특징

### ✅ **장점**
- **실시간 처리**: MQTT 비동기 메시지 처리
- **안정성**: 자동 재연결 및 오류 복구
- **확장성**: 새로운 AGV 추가 시 자동 대응
- **데이터 보존**: 이미지 및 로그 파일 영구 저장
- **모니터링**: 실시간 상태 추적 및 요약 출력

### ⚠️ **주의사항**
- MQTT 브로커가 localhost에서 실행되어야 함
- 이미지 저장 디스크 용량 모니터링 필요
- 네트워크 단절 시 데이터 손실 가능성
- 동시 다중 AGV 처리 시 성능 고려 필요

---

이러한 흐름으로 라즈베리파이가 중앙 서버와 AGV들 간의 효율적인 브릿지 역할을 수행합니다! 🎯