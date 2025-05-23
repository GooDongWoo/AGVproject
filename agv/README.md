# 🦾 로봇팔 통합 AGV 시스템

## 📋 시스템 개요

이제 AGV는 **로봇팔(JBArm)**과 **ArUco 마커 기반 물건 탐지**를 통해 정밀한 집기/놓기 작업을 수행할 수 있습니다.

## 🔄 업데이트된 작업 흐름

### 1. 집하 단계 (Phase 1)
```
라인 팔로잉 → 빨간색 영역 도착 → 라인 팔로잉 정지 
→ ArUco 마커 탐지 → 로봇팔 집기 → 라인 팔로잉 재시작
```

### 2. 배송 단계 (Phase 2)  
```
라인 팔로잉 → 파란색 영역 도착 → 라인 팔로잉 정지
→ 로봇팔 놓기 → 작업 완료
```

## 📁 필요한 파일 구조

```
agv/
├── main.ipynb              # 메인 시스템 (로봇팔 통합)
├── config.py               # 설정 파일 (로봇팔 설정 추가)  
├── mqtt_manager.py         # MQTT 통신 관리
├── road_following.py       # 라인 추종 (정지/재시작 지원)
├── area_detecting.py       # 영역 탐지 (로봇팔 통합)
├── SCSCtrl.py             # 서보 제어 스텁 (선택사항)
└── control/               # 로봇팔 제어 모듈
    ├── JBArm.py           # 로봇팔 제어
    ├── BoxDetector.py     # ArUco 마커 탐지
    ├── Kinematics.py      # 역기구학 계산
    └── example.ipynb      # 사용 예제
```

## 🎯 ArUco 마커 설정

### 마커 배치
- **마커 ID = 물건 인덱스** (0~10번)
- 각 물건에 고유한 ArUco 마커 부착
- 마커 크기: 30mm × 30mm (설정 가능)

### 마커 생성 예시
```python
import cv2

# ArUco 딕셔너리 생성
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# 마커 생성 (ID 0~10)
for marker_id in range(11):
    marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, 200)
    cv2.imwrite(f'marker_{marker_id}.png', marker_image)
```

## 🛠️ 설치 및 설정

### 1. 의존성 설치
```bash
# OpenCV ArUco 지원
pip install opencv-contrib-python

# NumPy (버전 호환성 확인)
pip install numpy

# 기존 JetBot 라이브러리
pip install jetbot
```

### 2. 로봇팔 캘리브레이션
```python
# control/example.ipynb 실행하여 로봇팔 테스트
from control.JBArm import JBArm

arm = JBArm()
arm.ready()  # 준비 위치로 이동
arm.grab()   # 집기 테스트
arm.release() # 놓기 테스트
```

### 3. 카메라 캘리브레이션
BoxDetector의 카메라 파라미터를 실제 카메라에 맞게 조정:
```python
# control/BoxDetector.py에서 수정
self.cam_intrinsic = np.array([
    [146.7755, 0, 151.9934],      # 실제 카메라에 맞게 수정
    [0, 196.3291, 134.7969],
    [0, 0, 1]
], dtype=np.float32)
```

## 🎮 사용 예시

### 명령 전송
```bash
# 물건 3번을 빨간 구역에서 파란 구역으로 이동
AGV> quick
입력: 1 AGV_1 red blue 5 3
```

### 예상 로그 출력
```
📦 물건 인덱스 설정: 3
🛣️ 라인 팔로잉 시작
🎯 집하 영역 도착 - 물건 3
⏸️ 라인 팔로잉 정지
🔍 물건 3 탐지 시작...
📍 물건 3 위치: [154.67586952  42.18133951 -71.8633672]
✅ 물건 3 집기 완료
🔄 물건 3 - 2단계(배송)로 전환
▶️ 라인 팔로잉 재시작
🎯 배송 영역 도착 - 물건 3
⏸️ 라인 팔로잉 정지
📦 물건 3 놓기 시작...
✅ 물건 3 놓기 완료
🏁 물건 3 작업 완료
```

## ⚙️ 주요 설정 파라미터

### config.py 설정
```python
# 로봇팔 관련
ROBOT_ARM_ENABLED = True           # 로봇팔 사용 여부
ARM_PICK_HEIGHT_OFFSET = 20        # 집기 전 높이 오프셋 (mm)
ARM_PLACE_HEIGHT_OFFSET = 50       # 놓기 전 높이 오프셋 (mm)
ARM_SAFE_HEIGHT = 100              # 안전 높이 (mm)
ARM_OPERATION_DELAY = 2.0          # 로봇팔 동작 대기 시간 (초)

# 물건 탐지 관련
OBJECT_DETECTION_TIMEOUT = 10.0    # 물건 탐지 타임아웃 (초)
MARKER_DETECTION_RETRIES = 5       # ArUco 마커 탐지 재시도 횟수
```

## 🔧 문제 해결

### 1. 로봇팔 초기화 실패
```bash
# SCSCtrl 모듈 확인
python -c "import SCSCtrl; print('OK')"

# 대안: 스텁 모듈 사용
cp SCSCtrl.py agv/  # 스텁 버전 복사
```

### 2. ArUco 마커 탐지 안됨
```python
# 마커 크기 조정
self.marker_sz = 50  # BoxDetector.py에서 크기 증가

# 조명 조건 개선
# 균일한 조명, 그림자 제거

# 카메라 해상도 확인
frame_resized = cv2.resize(frame, (640, 480))  # 해상도 증가
```

### 3. 로봇팔 동작 부정확
```python
# 좌표계 확인 및 오프셋 조정
self.off_r = 20      # 반지름 오프셋 조정  
self.off_z = -40     # Z축 오프셋 조정

# 변환 행렬 재캘리브레이션
T1 = self.transform_3d(0, 0, 0, 45, 0, 30)  # 파라미터 조정
```

## 🚀 고급 기능

### 1. 동적 집기 위치 계산
```python
def _calculate_pickup_position(self, marker_position):
    """마커 위치를 기반으로 최적 집기 위치 계산"""
    # 물건별 크기/형태 고려
    offset = self._get_item_offset(self.item_idx)
    return marker_position + offset
```

### 2. 충돌 회피
```python
def _safe_arm_movement(self, target_position):
    """안전한 로봇팔 이동 경로 계산"""
    # 중간 경유점을 통한 안전한 이동
    waypoints = self._calculate_safe_path(target_position)
    for wp in waypoints:
        self.robot_arm.move_to_xyz(wp)
```

### 3. 비전 기반 정밀 제어
```python
def _visual_feedback_pickup(self):
    """실시간 비전 피드백을 통한 정밀 집기"""
    while not self._is_gripped():
        current_pos = self._detect_object_realtime()
        self.robot_arm.adjust_position(current_pos)
```

## 📊 성능 최적화

### 1. 탐지 속도 향상
- 이미지 해상도 조정 (300×300 → 640×480)
- ROI(관심 영역) 설정으로 탐지 범위 제한
- 멀티스레딩으로 탐지와 제어 분리

### 2. 정확도 향상
- 다중 각도에서 마커 탐지
- 칼만 필터를 통한 위치 안정화
- 히스토리 기반 위치 예측

### 3. 안전성 강화
- 로봇팔 동작 범위 제한
- 비상 정지 기능 추가
- 충돌 감지 및 회피

---

## 🎯 실제 배포 체크리스트

- [ ] 로봇팔 하드웨어 연결 및 테스트
- [ ] ArUco 마커 인쇄 및 부착 (ID 0~10)
- [ ] 카메라 캘리브레이션 완료
- [ ] 작업 영역 색상 마커 설치
- [ ] 라인 추종 경로 설정
- [ ] 전체 시스템 통합 테스트
- [ ] 안전 장치 및 비상 정지 확인

**이제 AGV가 정밀한 로봇팔 제어로 물건을 안전하게 집고 배송할 수 있습니다! 🦾🚗💨**