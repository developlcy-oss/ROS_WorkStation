#include <iostream>
#include <iomanip>
#include <cmath>

class RobotBrake {
private:
    double velocity;        // 속도 (m/s)
    double friction;        // 마찰계수
    const double gravity = 9.81;

public:
    // 생성자
    RobotBrake(double v, double mu)
        : velocity(v), friction(mu) {}

    // 제동거리 계산
    double calculateStopDistance() const {
        return (velocity * velocity) / (2.0 * friction * gravity);
    }

    // 결과 출력
    void printResult() const {
        double distance = calculateStopDistance();

        std::cout << std::fixed << std::setprecision(3);
        std::cout << "속도: " << velocity << " m/s\n";
        std::cout << "마찰계수: " << friction << "\n";
        std::cout << "제동거리: " << distance << " m\n";
    }
};

int main() {
    double friction;
    double velocity;

    std::cout << "로봇의 속도(m/s)를 입력하세요: ";
    std::cin >> velocity;

    std::cout << "마찰계수를 입력하세요: ";
    std::cin >> friction;

    if (velocity < 0 || friction <= 0) {
        std::cerr << "잘못된 입력입니다.\n";
        return 1;
    }

    RobotBrake robot(velocity, friction);
    robot.printResult();

    return 0;
}