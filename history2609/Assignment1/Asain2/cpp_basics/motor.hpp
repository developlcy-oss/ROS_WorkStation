#ifndef MOTOR_HPP
#define MOTOR_HPP

class Motor {
private:
    int speed;

public:
    Motor();
    void setSpeed(int speed);
    int getSpeed() const;
};

#endif