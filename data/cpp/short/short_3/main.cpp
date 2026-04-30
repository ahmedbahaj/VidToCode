/******************************************************************************

                              Online C++ Compiler.
               Code, Compile, Run and Debug C++ program online.
Write your code in this editor and press "Run" button to compile and execute it.

*******************************************************************************/

#include <iostream>
using namespace std;

int linearsearch(int arr[], int size, int target){
    for(int i=0; i<size; i++){
        if(arr[i] == target){
            return i; // found the target
        }
    }
    
    return -1; // target doesn't exist
}

int main()
{
    int arr[] = {2, 6, 3, 0, 9, 5};
    int size = sizeof(arr) / sizeof(arr[0]);
    int target = 9;
    
    int result = linearsearch(arr, size, target);
    cout << result;

    return 0;
}