#ifndef SENSOR_HPP
#define SENSOR_HPP
#include<string>
#include <iostream>

class Sensor {
public:
virtual ~Sensor(){
 std::cout << "Sensor destructor" << std::endl;
}
virtual void read() = 0;
virtual std::string getName() const = 0; 

};

#endif