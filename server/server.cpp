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
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

// JSON 라이브러리 네임스페이스 사용
using json = nlohmann::json;

// 서버 설정
const int PORT = 5000;
const int MAX_CONNECTIONS = 5;
const int BUFFER_SIZE = 4096;

// 전역 변수
std::mutex clientsMutex;
std::vector<int> raspberryPiSockets;
std::map<int, std::string> socketToAddress; // 소켓 -> 주소 매핑
bool serverRunning = true;

// 색상 목록 (AGV 설정과 동일)
const std::vector<std::string> COLOR_LIST = {"red", "green", "blue", "purple", "yellow", "orange"};

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

// 연결된 라즈베리파이 목록 출력
void printConnectedRaspberryPis() {
    std::lock_guard<std::mutex> lock(clientsMutex);
    std::cout << "\n=== 연결된 라즈베리파이 목록 ===" << std::endl;
    if (raspberryPiSockets.empty()) {
        std::cout << "연결된 라즈베리파이가 없습니다." << std::endl;
    } else {
        for (size_t i = 0; i < raspberryPiSockets.size(); i++) {
            int socket = raspberryPiSockets[i];
            std::string address = socketToAddress[socket];
            std::cout << "[" << (i + 1) << "] " << address << " (소켓: " << socket << ")" << std::endl;
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
bool sendCommandToSpecificRaspberryPi(int socketIndex, const std::string& agvId, 
                                       const std::string& startColor, const std::string& endColor, 
                                       int delaySeconds, int itemIdx) {
    std::lock_guard<std::mutex> lock(clientsMutex);
    
    if (socketIndex < 0 || socketIndex >= static_cast<int>(raspberryPiSockets.size())) {
        std::cout << "잘못된 라즈베리파이 번호입니다." << std::endl;
        return false;
    }
    
    int clientSocket = raspberryPiSockets[socketIndex];
    
    try {
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
        
        // 명령 생성 (인덱스 사용)
        json command = {
            {"start", startIndex},
            {"end", endIndex},
            {"delays", delaySeconds},
            {"agv_id", agvId},
            {"timedata", getCurrentTimeString()},
            {"item_idx", itemIdx}
        };
        
        // 명령 전송
        std::string commandStr = command.dump();
        int sendResult = send(clientSocket, commandStr.c_str(), commandStr.length(), 0);
        
        if (sendResult < 0) {
            std::cout << "명령 전송 실패: " << strerror(errno) << std::endl;
            return false;
        } else {
            std::cout << "✅ 명령 전송 성공!" << std::endl;
            std::cout << "   대상: " << socketToAddress[clientSocket] << std::endl;
            std::cout << "   AGV ID: " << agvId << std::endl;
            std::cout << "   경로: " << startColor << "(" << startIndex << ") → " 
                      << endColor << "(" << endIndex << ")" << std::endl;
            std::cout << "   지연시간: " << delaySeconds << "초" << std::endl;
            std::cout << "   물건 인덱스: " << itemIdx << std::endl;
            std::cout << "   전송 데이터: " << commandStr << std::endl;
            return true;
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
    
    std::lock_guard<std::mutex> lock(clientsMutex);
    if (raspberryPiSockets.empty()) {
        return;
    }
    
    lock.~lock_guard(); // 수동으로 락 해제
    
    int raspberryPiIndex;
    std::string agvId, startColor, endColor;
    int delaySeconds, itemIdx;
    
    std::cout << "라즈베리파이 번호를 선택하세요 (1-" << raspberryPiSockets.size() << "): ";
    std::cin >> raspberryPiIndex;
    raspberryPiIndex--; // 0-based 인덱스로 변환
    
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
    
    sendCommandToSpecificRaspberryPi(raspberryPiIndex, agvId, startColor, endColor, delaySeconds, itemIdx);
}

// 빠른 명령 전송 (한 줄 입력)
void quickSendCommand() {
    printConnectedRaspberryPis();
    
    std::lock_guard<std::mutex> lock(clientsMutex);
    if (raspberryPiSockets.empty()) {
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
        sendCommandToSpecificRaspberryPi(raspberryPiIndex, agvId, startColor, endColor, delaySeconds, itemIdx);
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

// 클라이언트 처리 함수
void handleClient(int clientSocket, const std::string& clientAddr) {
    std::cout << "연결됨: " << clientAddr << std::endl;

    char buffer[BUFFER_SIZE];
    bool isRaspberryPi = false;

    try {
        // 초기 메시지 수신으로 클라이언트 유형 판별
        memset(buffer, 0, BUFFER_SIZE);
        int bytesReceived = recv(clientSocket, buffer, BUFFER_SIZE - 1, 0);
        
        if (bytesReceived <= 0) {
            std::cerr << "초기 데이터 수신 실패" << std::endl;
            close(clientSocket);
            return;
        }
        
        std::string dataStr(buffer);
        json clientData;
        
        try {
            clientData = json::parse(dataStr);
            // 클라이언트 유형 확인
            if (clientData.contains("client_type") && clientData["client_type"] == "raspberry_pi") {
                isRaspberryPi = true;
                std::cout << "라즈베리 파이 클라이언트 연결됨: " << clientAddr << std::endl;
                
                // 라즈베리 파이 소켓 목록에 추가
                {
                    std::lock_guard<std::mutex> lock(clientsMutex);
                    raspberryPiSockets.push_back(clientSocket);
                    socketToAddress[clientSocket] = clientAddr;
                }
                
                // 라즈베리 파이에게 연결 확인 응답
                json response = {
                    {"status", "connected"},
                    {"message", "라즈베리 파이 연결 성공"}
                };
                std::string responseStr = response.dump();
                send(clientSocket, responseStr.c_str(), responseStr.length(), 0);
            }
        }
        catch (const json::parse_error& e) {
            std::cerr << "JSON 파싱 오류: " << e.what() << std::endl;
            close(clientSocket);
            return;
        }
        
        // 연결 유지 및 데이터 수신
        while (serverRunning) {
            memset(buffer, 0, BUFFER_SIZE);
            int bytesReceived = recv(clientSocket, buffer, BUFFER_SIZE - 1, 0);

            if (bytesReceived <= 0) {
                break; // 연결 종료 또는 오류
            }

            // 수신 데이터 확인 (센서 데이터 등)
            std::cout << "📡 " << clientAddr << "로부터 데이터 수신: " << buffer << std::endl;
        }
    }
    catch (const std::exception& e) {
        std::cerr << "클라이언트 처리 오류: " << e.what() << std::endl;
    }

    // 라즈베리 파이 소켓 목록에서 제거
    if (isRaspberryPi) {
        std::lock_guard<std::mutex> lock(clientsMutex);
        raspberryPiSockets.erase(
            std::remove(raspberryPiSockets.begin(), raspberryPiSockets.end(), clientSocket),
            raspberryPiSockets.end()
        );
        socketToAddress.erase(clientSocket);
    }

    // 연결 종료
    close(clientSocket);
    std::cout << "연결 종료: " << clientAddr << std::endl;
}

int main() {
    // 소켓 생성
    int serverSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (serverSocket == -1) {
        std::cerr << "소켓 생성 실패" << std::endl;
        return 1;
    }

    // 소켓 옵션 설정 (재사용)
    int opt = 1;
    if (setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        std::cerr << "소켓 옵션 설정 실패" << std::endl;
        close(serverSocket);
        return 1;
    }

    // 서버 주소 설정
    struct sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY; // 모든 인터페이스에서 연결 허용
    serverAddr.sin_port = htons(PORT);

    // 바인딩
    if (bind(serverSocket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) < 0) {
        std::cerr << "바인딩 실패" << std::endl;
        close(serverSocket);
        return 1;
    }

    // 리스닝
    if (listen(serverSocket, MAX_CONNECTIONS) < 0) {
        std::cerr << "리스닝 실패" << std::endl;
        close(serverSocket);
        return 1;
    }

    std::cout << "🚀 AGV 명령 서버가 포트 " << PORT << "에서 실행 중..." << std::endl;
    
    // 사용자 입력 처리 스레드 시작
    std::thread inputThread(userInputHandler);
    inputThread.detach();

    // 메인 루프 - 클라이언트 연결 처리
    try {
        while (serverRunning) {
            struct sockaddr_in clientAddr;
            socklen_t clientAddrLen = sizeof(clientAddr);

            // 클라이언트 연결 수락 (논블로킹으로 설정하거나 타임아웃 설정)
            fd_set readfds;
            FD_ZERO(&readfds);
            FD_SET(serverSocket, &readfds);
            
            struct timeval timeout;
            timeout.tv_sec = 1;  // 1초 타임아웃
            timeout.tv_usec = 0;
            
            int activity = select(serverSocket + 1, &readfds, NULL, NULL, &timeout);
            
            if (activity < 0) {
                if (!serverRunning) break;
                continue;
            }
            
            if (activity == 0) {
                // 타임아웃 - 서버 종료 확인
                continue;
            }
            
            if (FD_ISSET(serverSocket, &readfds)) {
                int clientSocket = accept(serverSocket, (struct sockaddr*)&clientAddr, &clientAddrLen);
                if (clientSocket < 0) {
                    if (!serverRunning) break;
                    std::cerr << "연결 수락 실패" << std::endl;
                    continue;
                }

                // 클라이언트 주소 정보 가져오기
                char clientIp[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &(clientAddr.sin_addr), clientIp, INET_ADDRSTRLEN);
                std::string clientAddrStr = std::string(clientIp) + ":" + std::to_string(ntohs(clientAddr.sin_port));

                // 클라이언트 처리 스레드 생성
                std::thread clientThread(handleClient, clientSocket, clientAddrStr);
                clientThread.detach();
            }
        }
    }
    catch (const std::exception& e) {
        std::cerr << "서버 오류: " << e.what() << std::endl;
    }

    // 소켓 닫기
    close(serverSocket);
    std::cout << "서버가 종료되었습니다." << std::endl;

    return 0;
}