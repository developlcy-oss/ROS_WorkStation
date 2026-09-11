#include "imu.hpp"
#include <iostream>

Imu::Imu(){
    std::cout << "Imu 생성" << std::endl;
}

Imu::~Imu(){
    std::cout << "Imu 소멸" << std::endl;
}

void Imu::read(){
    std::cout << "Imu : reading distance data" << std::endl;
}

std::string Imu::getName() const
{
    return "Imu";
}


