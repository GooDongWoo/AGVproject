# AGV MQTT 클라이언트 서버 Makefile

# 컴파일러 설정
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2 -pthread

# 라이브러리 설정
LIBS = -lmosquitto -ljson

# 소스 파일
SRCFILE = server.cpp

# 실행 파일 이름
TARGET = mqtt_server

# 기본 타겟
all: $(TARGET)

# 실행 파일 빌드
$(TARGET): $(SRCFILE)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRCFILE) $(LIBS)
	@echo "✅ MQTT 클라이언트 서버 빌드 완료: $(TARGET)"

# 의존성 설치 (Ubuntu/Debian)
install-deps:
	@echo "📦 의존성 설치 중..."
	sudo apt-get update
	sudo apt-get install -y \
		g++ \
		libmosquitto-dev \
		nlohmann-json3-dev \
		mosquitto-clients
	@echo "✅ 의존성 설치 완료"

# 서버 실행
run: $(TARGET)
	@echo "🚀 MQTT 클라이언트 서버 실행 중..."
	@echo "주의: 외부 MQTT 브로커가 실행 중인지 확인하세요"
	./$(TARGET)

# MQTT 연결 테스트 (외부 브로커 필요)
test:
	@echo "🧪 MQTT 연결 테스트..."
	@echo "외부 MQTT 브로커 주소를 확인하세요"
	mosquitto_pub -h mqtt.broker.address -t "test/topic" -m "Hello MQTT" -u central_server -P AgvServer2025!

# 청소
clean:
	rm -f $(TARGET)
	@echo "🧹 빌드 파일 정리 완료"

# 도움말
help:
	@echo "AGV MQTT 클라이언트 서버 빌드 시스템"
	@echo ""
	@echo "⚠️  주의사항: 별도의 MQTT 브로커 서버가 필요합니다"
	@echo ""
	@echo "사용 가능한 명령어:"
	@echo "  make              - 서버 빌드"
	@echo "  make install-deps - 의존성 설치"
	@echo "  make run          - 서버 실행"
	@echo "  make test         - MQTT 연결 테스트"
	@echo "  make clean        - 빌드 파일 정리"
	@echo "  make help         - 이 도움말 표시"
	@echo ""
	@echo "설치 순서:"
	@echo "  1. 외부 MQTT 브로커 서버 준비"
	@echo "  2. server.cpp에서 브로커 주소 수정"
	@echo "  3. make install-deps"
	@echo "  4. make"
	@echo "  5. make run"

.PHONY: all install-deps run test clean help