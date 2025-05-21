#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <thread>
#include <mutex>
#include <chrono>
#include <ctime>
#include <cstring>
#include <functional>
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
const int MAX_CONNECTIONS = 3;
const int BUFFER_SIZE = 4096;

// AGV 상태 구조체
struct AgvStatus {
    json status;
    std::string lastUpdate;
};

// 전역 변수
std::map<std::string, AgvStatus> agvStatusMap;
std::map<int, std::thread> clientThreads;
std::mutex statusMutex; // 상태 맵 접근 보호용 뮤텍스

// 현재 시간을 문자열로 반환하는 함수
std::string getCurrentTimeString() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_time = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&now_time), "%Y-%m-%d %H:%M:%S");
    return ss.str();
}

// 클라이언트 처리 함수
void handleClient(int clientSocket, const std::string& clientAddr) {
    std::cout << "연결됨: " << clientAddr << std::endl;

    char buffer[BUFFER_SIZE];

    try {
        while (true) {
            // 데이터 수신
            memset(buffer, 0, BUFFER_SIZE);
            int bytesReceived = recv(clientSocket, buffer, BUFFER_SIZE - 1, 0);

            if (bytesReceived <= 0) {
                break; // 연결 종료 또는 오류
            }

            // JSON 파싱
            std::string dataStr(buffer);
            json agvData;

            try {
                agvData = json::parse(dataStr);
                std::string agvId = agvData["agv_id"];

                // AGV 상태 업데이트
                std::lock_guard<std::mutex> lock(statusMutex);
                agvStatusMap[agvId] = {
                    agvData,
                    getCurrentTimeString()
                };

                std::cout << "AGV " << agvId << " 상태 업데이트: " << agvData.dump() << std::endl;

                // 명령 생성 (예시)
                json command = {
                    {"command_id", 1},
                    {"agv_id", agvId},
                    {"action", "move"},
                    {"parameters", {{"x", 100}, {"y", 200}}}
                };

                // 명령 전송
                std::string commandStr = command.dump();
                send(clientSocket, commandStr.c_str(), commandStr.length(), 0);

            }
            catch (const json::parse_error& e) {
                std::cerr << "JSON 파싱 오류: " << e.what() << std::endl;
            }
        }
    }
    catch (const std::exception& e) {
        std::cerr << "클라이언트 처리 오류: " << e.what() << std::endl;
    }

    // 연결 종료
    close(clientSocket);
    std::cout << "연결 종료: " << clientAddr << std::endl;
}

// AGV 상태 출력 함수
void showAgvStatus() {
    while (true) {
        {
            std::lock_guard<std::mutex> lock(statusMutex);

            std::cout << "\n=== AGV 운용 현황 ===" << std::endl;
            for (const auto& pair : agvStatusMap) {
                std::cout << "AGV ID: " << pair.first << std::endl;
                std::cout << "상태: " << pair.second.status.dump(4) << std::endl;
                std::cout << "마지막 업데이트: " << pair.second.lastUpdate << std::endl;
                std::cout << "------------------------------" << std::endl;
            }
        }

        // 10초마다 업데이트
        std::this_thread::sleep_for(std::chrono::seconds(10));
    }
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

    std::cout << "서버가 포트 " << PORT << "에서 실행 중..." << std::endl;

    // AGV 상태 모니터링 스레드 시작
    std::thread statusThread(showAgvStatus);
    statusThread.detach();

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

