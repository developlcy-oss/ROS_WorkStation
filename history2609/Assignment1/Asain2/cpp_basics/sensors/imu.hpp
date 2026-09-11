#ifndef IMU_HPP
#define IMU_HPP
#include "sensor.hpp"

class Imu : public Sensor {

public:
Imu();
~Imu() override;

void read() override;
std::string getName() const override;

};

#endif