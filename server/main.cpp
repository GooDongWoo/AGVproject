#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <thread>
#include <mutex>
#include <chrono>
#include <ctime>
#include <cstring>
#include <random>
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
std::random_device rd;
std::mt19937 gen;

// 현재 시간을 문자열로 반환하는 함수
std::string getCurrentTimeString() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_time = std::chrono::system_clock::to_time_t(now);
    char timeStr[20];
    std::strftime(timeStr, sizeof(timeStr), "%Y-%m-%d %H:%M:%S", std::localtime(&now_time));
    return std::string(timeStr);
}

// 라즈베리 파이에 명령 전송 함수
void sendCommandToRaspberryPi(int clientSocket, const std::string& agvId) {
    try {
        // 랜덤 숫자 생성기 초기화
        std::uniform_int_distribution<> flagDis(0, 1);     // 시작 플래그 (0 또는 1)
        std::uniform_int_distribution<> locDis(0, 5);      // 위치 (0~5)
        std::uniform_int_distribution<> delayDis(0, 100);  // 지연 시간 (0~100초)

        // 시작 플래그, 위치, 지연 시간 랜덤 생성
        int startFlag = flagDis(gen);
        int startLocation = locDis(gen);
        int destLocation = locDis(gen);
        int delaySeconds = delayDis(gen);
        
        // 명령 생성
        json command = {
            {"start_flag", startFlag},
            {"start_location", startLocation},
            {"destination", destLocation},
            {"delay_seconds", delaySeconds},
            {"agv_id", agvId},
            {"timestamp", getCurrentTimeString()}
        };

        // 명령 전송
        std::string commandStr = command.dump();
        int sendResult = send(clientSocket, commandStr.c_str(), commandStr.length(), 0);
        
        if (sendResult < 0) {
            std::cerr << "명령 전송 실패: " << strerror(errno) << std::endl;
        } else {
            std::cout << "AGV " << agvId << "에 명령 전송 완료: " << commandStr << std::endl;
        }
    }
    catch (const std::exception& e) {
        std::cerr << "명령 전송 중 오류 발생: " << e.what() << std::endl;
    }
}

// 모든 라즈베리 파이에 주기적으로 명령 전송하는 함수
void periodicCommandSender() {
    std::vector<std::string> agvIds = {"AGV_1", "AGV_2"};
    
    while (true) {
        std::this_thread::sleep_for(std::chrono::minutes(1)); // 1분 간격
        
        std::lock_guard<std::mutex> lock(clientsMutex);
        if (raspberryPiSockets.empty()) {
            std::cout << "연결된 라즈베리 파이가 없습니다." << std::endl;
            continue;
        }
        
        // 각 AGV에 대해 명령 생성 및 전송
        for (const auto& agvId : agvIds) {
            for (int socket : raspberryPiSockets) {
                sendCommandToRaspberryPi(socket, agvId);
            }
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
        
        while (true) {
            // 데이터 수신
            memset(buffer, 0, BUFFER_SIZE);
            int bytesReceived = recv(clientSocket, buffer, BUFFER_SIZE - 1, 0);

            if (bytesReceived <= 0) {
                break; // 연결 종료 또는 오류
            }

            // 수신 데이터 확인 (간단한 로깅만)
            std::cout << "데이터 수신: " << buffer << std::endl;
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
    }

    // 연결 종료
    close(clientSocket);
    std::cout << "연결 종료: " << clientAddr << std::endl;
}

int main() {
    // 랜덤 숫자 생성기 초기화
    gen = std::mt19937(rd());
    
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

    std::cout << "서버가 포트 " << PORT << "에서 실행 중..." << std::endl;
    
    // 주기적 명령 전송 스레드 시작
    std::thread commandThread(periodicCommandSender);
    commandThread.detach();

    // 메인 루프
    try {
        while (true) {
            struct sockaddr_in clientAddr;
            socklen_t clientAddrLen = sizeof(clientAddr);

            // 클라이언트 연결 수락
            int clientSocket = accept(serverSocket, (struct sockaddr*)&clientAddr, &clientAddrLen);
            if (clientSocket < 0) {
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
    catch (const std::exception& e) {
        std::cerr << "서버 오류: " << e.what() << std::endl;
    }

    // 소켓 닫기
    close(serverSocket);

    return 0;
}