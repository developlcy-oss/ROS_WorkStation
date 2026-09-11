#ifndef LIDAR_HPP
#define LIDAR_HPP
#include "sensor.hpp"

class Lidar : public Sensor {

public:
Lidar();
~Lidar() override;

void read() override;
std::string getName() const override;

};

#endif