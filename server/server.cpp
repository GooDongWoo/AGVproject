#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <thread>
#include <mutex>
#include <chrono>
#include <ctime>
#include <cstring>
#include <sstream>
#include <nlohmann/json.hpp>
#include <mosquitto.h>

// JSON 라이브러리 네임스페이스 사용
using json = nlohmann::json;

// 외부 MQTT 브로커 설정 (별도 브로커 서버 필요)
const std::string MQTT_BROKER_HOST = "mqtt.broker.address";  // 실제 브로커 주소로 변경
const int MQTT_BROKER_PORT = 1883;
const std::string MQTT_USERNAME = "central_server";
const std::string MQTT_PASSWORD = "AgvServer2025!";

// MQTT 토픽
const std::string COMMAND_TOPIC_PREFIX = "server/commands/";
const std::string STATUS_TOPIC_PREFIX = "raspberrypi/status/";
const std::string HEARTBEAT_TOPIC = "raspberrypi/heartbeat";

// 서버 설정
const std::vector<std::string> COLOR_LIST = {"red", "green", "blue", "purple", "yellow", "orange"};

// 전역 변수
std::mutex connectedRaspberryPisMutex;
std::map<std::string, std::chrono::system_clock::time_point> connectedRaspberryPis; // ID -> 마지막 하트비트
bool serverRunning = true;
struct mosquitto *mosq = nullptr;

// 현재 시간을 문자열로 반환하는 함수
std::string getCurrentTimeString() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_time = std::chrono::system_clock::to_time_t(now);
    char timeStr[20];
    std::strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", std::localtime(&now_time));
    return std::string(timeStr);
}

// 색상 이름을 인덱스로 변환
int getColorIndex(const std::string& colorName) {
    for (size_t i = 0; i < COLOR_LIST.size(); i++) {
        if (COLOR_LIST[i] == colorName) {
            return static_cast<int>(i);
        }
    }
    return -1; // 찾지 못한 경우
}

// MQTT 연결 콜백
void on_connect(struct mosquitto *mosq, void *userdata, int result) {
    if (result == 0) {
        std::cout << "✅ MQTT 브로커 연결 성공" << std::endl;
        
        // 상태 및 하트비트 토픽 구독
        mosquitto_subscribe(mosq, nullptr, (STATUS_TOPIC_PREFIX + "+").c_str(), 1);
        mosquitto_subscribe(mosq, nullptr, HEARTBEAT_TOPIC.c_str(), 1);
        
        std::cout << "📡 토픽 구독 완료" << std::endl;
    } else {
        std::cout << "❌ MQTT 연결 실패: " << result << std::endl;
    }
}

// MQTT 메시지 수신 콜백
void on_message(struct mosquitto *mosq, void *userdata, const struct mosquitto_message *message) {
    std::string topic(message->topic);
    std::string payload((char*)message->payload, message->payloadlen);
    
    try {
        json messageData = json::parse(payload);
        
        // 하트비트 처리
        if (topic == HEARTBEAT_TOPIC) {
            std::string raspberryPiId = messageData["raspberry_pi_id"];
            {
                std::lock_guard<std::mutex> lock(connectedRaspberryPisMutex);
                connectedRaspberryPis[raspberryPiId] = std::chrono::system_clock::now();
            }
            std::cout << "💓 하트비트 수신: " << raspberryPiId << std::endl;
            return;
        }
        
        // 상태 메시지 처리
        if (topic.find(STATUS_TOPIC_PREFIX) == 0) {
            std::string raspberryPiId = topic.substr(STATUS_TOPIC_PREFIX.length());
            std::cout << "📊 상태 수신 [" << raspberryPiId << "]: " << messageData.dump() << std::endl;
            return;
        }
        
    } catch (const json::parse_error& e) {
        std::cout << "❌ JSON 파싱 오류: " << e.what() << std::endl;
    }
}

// 연결된 라즈베리파이 목록 출력
void printConnectedRaspberryPis() {
    std::lock_guard<std::mutex> lock(connectedRaspberryPisMutex);
    std::cout << "\n=== 연결된 라즈베리파이 목록 ===" << std::endl;
    
    auto now = std::chrono::system_clock::now();
    if (connectedRaspberryPis.empty()) {
        std::cout << "연결된 라즈베리파이가 없습니다." << std::endl;
    } else {
        int index = 1;
        for (const auto& pair : connectedRaspberryPis) {
            auto timeDiff = std::chrono::duration_cast<std::chrono::seconds>(now - pair.second).count();
            std::string status = (timeDiff < 30) ? "🟢 온라인" : "🔴 오프라인";
            std::cout << "[" << index << "] " << pair.first << " - " << status 
                      << " (마지막 하트비트: " << timeDiff << "초 전)" << std::endl;
            index++;
        }
    }
    std::cout << "==============================\n" << std::endl;
}

// 도움말 출력
void printHelp() {
    std::cout << "\n=== AGV 명령어 도움말 ===" << std::endl;
    std::cout << "list        - 연결된 라즈베리파이 목록 보기" << std::endl;
    std::cout << "send        - AGV에 명령 전송 (대화형)" << std::endl;
    std::cout << "quick       - 빠른 명령 전송 (한 줄 입력)" << std::endl;
    std::cout << "colors      - 사용 가능한 색상 목록 보기" << std::endl;
    std::cout << "help        - 이 도움말 보기" << std::endl;
    std::cout << "exit        - 서버 종료" << std::endl;
    std::cout << "\n색상 목록: ";
    for (size_t i = 0; i < COLOR_LIST.size(); i++) {
        std::cout << COLOR_LIST[i];
        if (i < COLOR_LIST.size() - 1) std::cout << ", ";
    }
    std::cout << "\n물건 인덱스: 0-10 (총 11개 물건)" << std::endl;
    std::cout << "========================\n" << std::endl;
}

// 특정 라즈베리파이에 명령 전송
bool sendCommandToRaspberryPi(const std::string& raspberryPiId, const std::string& agvId, 
                              const std::string& startColor, const std::string& endColor, 
                              int delaySeconds, int itemIdx) {
    
    // 색상을 인덱스로 변환
    int startIndex = getColorIndex(startColor);
    int endIndex = getColorIndex(endColor);
    
    if (startIndex == -1) {
        std::cout << "잘못된 시작 색상: " << startColor << std::endl;
        return false;
    }
    if (endIndex == -1) {
        std::cout << "잘못된 끝 색상: " << endColor << std::endl;
        return false;
    }
    
    try {
        // 명령 생성 (인덱스 사용)
        json command = {
            {"start", startIndex},
            {"end", endIndex},
            {"delays", delaySeconds},
            {"agv_id", agvId},
            {"timedata", getCurrentTimeString()},
            {"item_idx", itemIdx}
        };
        
        // MQTT 토픽 생성
        std::string topic = COMMAND_TOPIC_PREFIX + raspberryPiId;
        std::string commandStr = command.dump();
        
        // MQTT로 명령 전송
        int result = mosquitto_publish(mosq, nullptr, topic.c_str(), 
                                      commandStr.length(), commandStr.c_str(), 1, false);
        
        if (result == MOSQ_ERR_SUCCESS) {
            std::cout << "✅ 명령 전송 성공!" << std::endl;
            std::cout << "   대상: " << raspberryPiId << std::endl;
            std::cout << "   AGV ID: " << agvId << std::endl;
            std::cout << "   경로: " << startColor << "(" << startIndex << ") → " 
                      << endColor << "(" << endIndex << ")" << std::endl;
            std::cout << "   지연시간: " << delaySeconds << "초" << std::endl;
            std::cout << "   물건 인덱스: " << itemIdx << std::endl;
            std::cout << "   토픽: " << topic << std::endl;
            std::cout << "   전송 데이터: " << commandStr << std::endl;
            return true;
        } else {
            std::cout << "명령 전송 실패: " << mosquitto_strerror(result) << std::endl;
            return false;
        }
    }
    catch (const std::exception& e) {
        std::cout << "명령 전송 중 오류 발생: " << e.what() << std::endl;
        return false;
    }
}

// 대화형 명령 전송
void interactiveSendCommand() {
    printConnectedRaspberryPis();
    
    std::lock_guard<std::mutex> lock(connectedRaspberryPisMutex);
    if (connectedRaspberryPis.empty()) {
        return;
    }
    
    // 온라인 상태 라즈베리파이만 필터링
    std::vector<std::string> onlineRaspberryPis;
    auto now = std::chrono::system_clock::now();
    for (const auto& pair : connectedRaspberryPis) {
        auto timeDiff = std::chrono::duration_cast<std::chrono::seconds>(now - pair.second).count();
        if (timeDiff < 30) {
            onlineRaspberryPis.push_back(pair.first);
        }
    }
    
    if (onlineRaspberryPis.empty()) {
        std::cout << "온라인 상태인 라즈베리파이가 없습니다." << std::endl;
        return;
    }
    
    lock.~lock_guard(); // 수동으로 락 해제
    
    int raspberryPiIndex;
    std::string agvId, startColor, endColor;
    int delaySeconds, itemIdx;
    
    std::cout << "라즈베리파이 번호를 선택하세요 (1-" << onlineRaspberryPis.size() << "): ";
    std::cin >> raspberryPiIndex;
    raspberryPiIndex--; // 0-based 인덱스로 변환
    
    if (raspberryPiIndex < 0 || raspberryPiIndex >= static_cast<int>(onlineRaspberryPis.size())) {
        std::cout << "잘못된 라즈베리파이 번호입니다." << std::endl;
        return;
    }
    
    std::string selectedRaspberryPi = onlineRaspberryPis[raspberryPiIndex];
    
    std::cout << "AGV ID를 입력하세요: ";
    std::cin >> agvId;
    
    std::cout << "시작 색상을 입력하세요 (" << COLOR_LIST[0];
    for (size_t i = 1; i < COLOR_LIST.size(); i++) {
        std::cout << ", " << COLOR_LIST[i];
    }
    std::cout << "): ";
    std::cin >> startColor;
    
    std::cout << "끝 색상을 입력하세요: ";
    std::cin >> endColor;
    
    std::cout << "지연 시간(초)을 입력하세요: ";
    std::cin >> delaySeconds;
    
    std::cout << "물건 인덱스를 입력하세요 (0-10): ";
    std::cin >> itemIdx;
    
    sendCommandToRaspberryPi(selectedRaspberryPi, agvId, startColor, endColor, delaySeconds, itemIdx);
}

// 빠른 명령 전송 (한 줄 입력)
void quickSendCommand() {
    printConnectedRaspberryPis();
    
    std::lock_guard<std::mutex> lock(connectedRaspberryPisMutex);
    if (connectedRaspberryPis.empty()) {
        return;
    }
    
    // 온라인 상태 라즈베리파이만 필터링
    std::vector<std::string> onlineRaspberryPis;
    auto now = std::chrono::system_clock::now();
    for (const auto& pair : connectedRaspberryPis) {
        auto timeDiff = std::chrono::duration_cast<std::chrono::seconds>(now - pair.second).count();
        if (timeDiff < 30) {
            onlineRaspberryPis.push_back(pair.first);
        }
    }
    
    if (onlineRaspberryPis.empty()) {
        std::cout << "온라인 상태인 라즈베리파이가 없습니다." << std::endl;
        return;
    }
    
    lock.~lock_guard();
    
    std::cout << "형식: <라즈베리파이번호> <AGV_ID> <시작색상> <끝색상> <지연시간> <물건인덱스>" << std::endl;
    std::cout << "예시: 1 AGV_1 red blue 5 3" << std::endl;
    std::cout << "입력: ";
    
    std::string line;
    std::cin.ignore(); // 이전 입력 버퍼 클리어
    std::getline(std::cin, line);
    
    std::istringstream iss(line);
    int raspberryPiIndex;
    std::string agvId, startColor, endColor;
    int delaySeconds, itemIdx;
    
    if (iss >> raspberryPiIndex >> agvId >> startColor >> endColor >> delaySeconds >> itemIdx) {
        raspberryPiIndex--; // 0-based 인덱스로 변환
        
        if (raspberryPiIndex >= 0 && raspberryPiIndex < static_cast<int>(onlineRaspberryPis.size())) {
            std::string selectedRaspberryPi = onlineRaspberryPis[raspberryPiIndex];
            sendCommandToRaspberryPi(selectedRaspberryPi, agvId, startColor, endColor, delaySeconds, itemIdx);
        } else {
            std::cout << "잘못된 라즈베리파이 번호입니다." << std::endl;
        }
    } else {
        std::cout << "입력 형식이 올바르지 않습니다." << std::endl;
    }
}

// 사용자 입력 처리 스레드
void userInputHandler() {
    std::string command;
    
    std::cout << "AGV 명령 서버가 시작되었습니다. 'help'를 입력하면 도움말을 볼 수 있습니다." << std::endl;
    
    while (serverRunning) {
        std::cout << "AGV> ";
        std::cin >> command;
        
        if (command == "exit") {
            std::cout << "서버를 종료합니다..." << std::endl;
            serverRunning = false;
            break;
        }
        else if (command == "help") {
            printHelp();
        }
        else if (command == "list") {
            printConnectedRaspberryPis();
        }
        else if (command == "colors") {
            std::cout << "\n사용 가능한 색상: ";
            for (size_t i = 0; i < COLOR_LIST.size(); i++) {
                std::cout << COLOR_LIST[i] << "(" << i << ")";
                if (i < COLOR_LIST.size() - 1) std::cout << ", ";
            }
            std::cout << "\n물건 인덱스: 0-10" << std::endl;
            std::cout << "\n" << std::endl;
        }
        else if (command == "send") {
            interactiveSendCommand();
        }
        else if (command == "quick") {
            quickSendCommand();
        }
        else {
            std::cout << "알 수 없는 명령입니다. 'help'를 입력하여 도움말을 확인하세요." << std::endl;
        }
    }
}

// 하트비트 정리 스레드
void heartbeatCleanupThread() {
    while (serverRunning) {
        std::this_thread::sleep_for(std::chrono::seconds(60)); // 1분마다 정리
        
        std::lock_guard<std::mutex> lock(connectedRaspberryPisMutex);
        auto now = std::chrono::system_clock::now();
        
        auto it = connectedRaspberryPis.begin();
        while (it != connectedRaspberryPis.end()) {
            auto timeDiff = std::chrono::duration_cast<std::chrono::seconds>(now - it->second).count();
            if (timeDiff > 300) { // 5분 이상 비활성화
                std::cout << "🗑️ 비활성 라즈베리파이 제거: " << it->first << std::endl;
                it = connectedRaspberryPis.erase(it);
            } else {
                ++it;
            }
        }
    }
}

int main() {
    // Mosquitto 라이브러리 초기화
    mosquitto_lib_init();
    
    // MQTT 클라이언트 생성
    mosq = mosquitto_new("central_server", true, nullptr);
    if (!mosq) {
        std::cerr << "MQTT 클라이언트 생성 실패" << std::endl;
        mosquitto_lib_cleanup();
        return 1;
    }
    
    // 인증 설정
    mosquitto_username_pw_set(mosq, MQTT_USERNAME.c_str(), MQTT_PASSWORD.c_str());
    
    // 콜백 설정
    mosquitto_connect_callback_set(mosq, on_connect);
    mosquitto_message_callback_set(mosq, on_message);
    
    // 브로커 연결
    int result = mosquitto_connect(mosq, MQTT_BROKER_HOST.c_str(), MQTT_BROKER_PORT, 60);
    if (result != MOSQ_ERR_SUCCESS) {
        std::cerr << "MQTT 브로커 연결 실패: " << mosquitto_strerror(result) << std::endl;
        mosquitto_destroy(mosq);
        mosquitto_lib_cleanup();
        return 1;
    }
    
    std::cout << "🚀 AGV 명령 서버가 시작되었습니다..." << std::endl;
    std::cout << "MQTT 브로커: " << MQTT_BROKER_HOST << ":" << MQTT_BROKER_PORT << std::endl;
    
    // MQTT 루프 시작
    mosquitto_loop_start(mosq);
    
    // 하트비트 정리 스레드 시작
    std::thread cleanupThread(heartbeatCleanupThread);
    cleanupThread.detach();
    
    // 사용자 입력 처리 시작
    userInputHandler();
    
    // 정리
    mosquitto_loop_stop(mosq, true);
    mosquitto_destroy(mosq);
    mosquitto_lib_cleanup();
    
    std::cout << "서버가 종료되었습니다." << std::endl;
    return 0;
}