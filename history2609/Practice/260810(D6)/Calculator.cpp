#include <string>
#include <iostream>

class Calculator {

private:
int result = 0 ;
std::string typeCode = "";

public:
int add (int firstNum, int secondNum) {
    std::cout << " 결과: " << firstNum + secondNum << std::endl;
      
    return 0;
}

int minus (int firstNum, int secondNum) {
    std::cout << " 결과: " << firstNum - secondNum << std::endl;

    return 0;
}

int multiple (int firstNum, int secondNum) {
    std::cout << " 결과: " << firstNum * secondNum << std::endl;

    return 0;
}

int division (int firstNum, int secondNum) {
    std::cout << " 결과: " << firstNum / secondNum << std::endl;

    return 0;
    }

bool typeValid(char typeCode) {
    
    if(typeCode == 'A') {
        return true;
    }
    
    else if(typeCode == 'B') {
        return true;
    }

    else if(typeCode == 'C') {
        return true;
    }

    else if(typeCode == 'D') {
        return true;
    }

    else {
        return false;
    }

}

bool numberValid(int firstNum, int secondNum, char typeCode) {

    if(typeCode == 'A') {
        add(firstNum, secondNum);
        return true;
    }
    
        else if (typeCode == 'B') {
        minus(firstNum, secondNum);
        return true;
    }

        else if(typeCode == 'C') {
        multiple(firstNum, secondNum);
        return true; 
    }

        else if(typeCode == 'D') {
        division(firstNum, secondNum);
        return true;
    }
    else {
        return false;
    }

}
};

int main () {

    Calculator calculator;
    char typeCode;

    while (true)
    {
        std::cout << "계산 타입 입력 : 더하기 = A, 빼기 = B, ""곱하기 = C, 나누기 = D"
                  << std::endl;
                  
        std::cin >> typeCode;
        typeCode = std::toupper(typeCode);

        if (calculator.typeValid(typeCode))
            break;

        std::cout << "잘못된 계산 타입입니다. 다시 입력해주세요."
                  << std::endl;
    }

    int firstNum;
    int secondNum;

while (true)
{
    std::cout << "첫번째 숫자를 입력하세요: ";

    if (!(std::cin >> firstNum))
    {
        std::cout << "숫자가 아닙니다. 다시 입력해주세요."
                  << std::endl;

        std::cin.clear();
        std::cin.ignore(1000, '\n');

        continue;
    }

    std::cout << "두번째 숫자를 입력하세요: ";

    if (!(std::cin >> secondNum))
    {
        std::cout << "숫자가 아닙니다. 다시 입력해주세요."
                  << std::endl;

        std::cin.clear();
        std::cin.ignore(1000, '\n');

        continue;
    }

    if (calculator.numberValid(firstNum, secondNum, typeCode))
        break;

}
    return 0;
}
