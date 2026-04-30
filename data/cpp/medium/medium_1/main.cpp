#include <iostream>
using namespace std;

class Phone{
    string p_name;
    string p_size;
    
public:
    Phone(string name, string size) {
        p_name = name;
        p_size = size;
    }
    
    void makeCall() {
        cout << "Making Call Using " << p_name << endl;
    }
    
    void receiveCall() {
        cout << "Receiving Call Using " << p_name <<endl;
    }
    
};

int main()
{
    Phone iPhone("Iphone_X", "1000x500");
    iPhone.makeCall();
    iPhone.receiveCall();
    
    cout << endl;
    
    Phone gPixel("Google Pixel 2 XL", "2000x700");
    gPixel.makeCall();
    gPixel.receiveCall();
    return 0;
}