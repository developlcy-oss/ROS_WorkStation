#include "motor.hpp"

//문제 1-4번 확인용 주석입니다.
Motor::Motor()
    : speed(0)
{
}

void Motor::setSpeed(int speed)
{
    this->speed = speed;
}

int Motor::getSpeed() const
{
    return speed;
}