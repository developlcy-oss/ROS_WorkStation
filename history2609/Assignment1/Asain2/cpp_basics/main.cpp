#include <iostream>
#include "motor.hpp"

int main()
{
    Motor motor;

    motor.setSpeed(50);

    std::cout << "Motor speed: "
              << motor.getSpeed()
              << std::endl;

    return 0;
}