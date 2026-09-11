#include "lidar.hpp"
#include "imu.hpp"
#include "sensor.hpp"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

// --------------------------------------------------
// clamp 함수 템플릿
// --------------------------------------------------
template <typename T>
T clamp(T value, T min_value, T max_value)
{
    if (value < min_value) {
        return min_value;
    }

    if (value > max_value) {
        return max_value;
    }

    return value;
}


// --------------------------------------------------
// 측정 데이터
// --------------------------------------------------
struct Measurement
{
    double x;
    double y;
};


// --------------------------------------------------
// 목표점까지 거리 계산
// --------------------------------------------------
double distanceToTarget(
    const Measurement& measurement,
    const Measurement& target)
{
    double dx = measurement.x - target.x;
    double dy = measurement.y - target.y;

    return std::sqrt(dx * dx + dy * dy);
}


// --------------------------------------------------
// 메모리 누수 재현
// --------------------------------------------------
void memoryLeak()
{
    std::cout << "\n===== Memory Leak Test =====" << std::endl;

    Sensor* sensor = new Lidar();

    // 의도적으로 delete하지 않음
    // delete sensor;

    std::cout << "Memory leak test finished." << std::endl;
}


// --------------------------------------------------
// make_unique를 이용한 메모리 관리
// --------------------------------------------------
void noMemoryLeak()
{
    std::cout << "\n===== make_unique Test =====" << std::endl;

    auto sensor = std::make_unique<Lidar>();

    std::cout << "make_unique test finished." << std::endl;
}


// --------------------------------------------------
// main
// --------------------------------------------------
int main()
{
    // ==================================================
    // 1. 다형성 루프
    // ==================================================
    std::cout << "===== 다형성 Test =====" << std::endl;

    std::vector<std::unique_ptr<Sensor>> sensors;

    sensors.push_back(std::make_unique<Lidar>());
    sensors.push_back(std::make_unique<Imu>());

    for (const auto& sensor : sensors) {
        std::cout << "[" << sensor->getName() << "] ";
        sensor->read();
    }

    // ==================================================
    // 2. 스택 객체와 힙 객체의 소멸 시점
    // ==================================================
    {
    std::cout << "\n===== 객체 생성 =====" << std::endl;

    Lidar stackLidar;
    auto smartImu = std::make_unique<Imu>();

    std::cout << "\n===== 객체 사용 =====" << std::endl;

    stackLidar.read();
    smartImu->read();

    std::cout << "\n===== 객체 소멸 직전 =====" << std::endl;
}

    // ==================================================
    // 3. unordered_map
    // ==================================================
    std::cout << "\n===== unordered_map Test =====" << std::endl;

    std::unordered_map<std::string, Measurement> latestMeasurements;

    latestMeasurements["Lidar"] = {1.0, 2.0};
    latestMeasurements["Imu"] = {0.2, 0.3};

    std::cout << "Latest Lidar: ("
              << latestMeasurements["Lidar"].x
              << ", "
              << latestMeasurements["Lidar"].y
              << ")" << std::endl;

    std::cout << "Latest Imu: ("
              << latestMeasurements["Imu"].x
              << ", "
              << latestMeasurements["Imu"].y
              << ")" << std::endl;

    // ==================================================
    // 4. vector + count_if
    // ==================================================
    std::cout << "\n===== count_if Test =====" << std::endl;

    Measurement target{0.0, 0.0};

    std::vector<Measurement> logs = {
        {0.1, 0.1},
        {0.3, 0.4},
        {1.0, 1.0},
        {0.2, 0.2},
        {0.8, 0.1}
    };

    int count = std::count_if(
        logs.begin(),
        logs.end(),
        [&target](const Measurement& measurement) {
            return distanceToTarget(measurement, target) <= 0.5;
        }
    );

    std::cout << "0.5 이내의 측정 기록: "
              << count
              << "개"
              << std::endl;

    // ==================================================
    // 5. clamp
    // ==================================================
    std::cout << "\n===== clamp Test =====" << std::endl;

    double speed = 15.5;
    int pixel = 300;

    double clampedSpeed = clamp(speed, 0.0, 10.0);
    int clampedPixel = clamp(pixel, 0, 255);

    std::cout << "속도: "
              << speed
              << " -> "
              << clampedSpeed
              << std::endl;

    std::cout << "픽셀: "
              << pixel
              << " -> "
              << clampedPixel
              << std::endl;


    // ==================================================
    // 6. 메모리 누수 테스트
    // ==================================================

    // 누수 검출 실험 시 실행
    //memoryLeak();

    // 수정 후 make_unique 사용
    noMemoryLeak();

    return 0;
}