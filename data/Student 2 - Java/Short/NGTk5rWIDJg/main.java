public class sampleclass {
    public static void main(String[] args) {

    int arr[]={1 , 45, 60, 100 ,0,5,5,5};

    int n=5;
    int f=0;
    for(int i=0;i<arr.length;i++)
    {
        if(arr[i]==n)
        {
            f=1;
            System.out.printf("Element found in index %d \n",i);
            break;
        }
    }
    if(f==0)
    {
        System.out.print("Element not found");
    }
}}