

#include <iostream>
using namespace std;


int linearsearch(int arr[], int size, int target){
    for(int i=0; i<size; i++){
        if(arr[i] == target){
            return i;
        }
    }

    return -1;
}



int main(){
    int arr[] = {2, 6, 3, 0, 9, 5};
    int size = sizeof(arr) / sizeof(arr[0]);
    int target = 10;

    int result = linearsearch(arr, size, target);
    cout << result;



    return 0;
}