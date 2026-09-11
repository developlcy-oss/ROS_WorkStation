#include "lidar.hpp"
#include <iostream>

Lidar::Lidar(){
    std::cout << "Lidar 생성" << std::endl;
}

Lidar::~Lidar(){
    std::cout << "Lidar 소멸" << std::endl;
}

void Lidar::read(){
    std::cout << "Lidar : reading distance data" << std::endl;
}

std::string Lidar::getName() const
{
    return "Lidar";
}
