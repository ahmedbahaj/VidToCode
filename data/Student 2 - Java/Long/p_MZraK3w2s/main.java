public class Searching {

    public static int binarySearch(int[] a, int key) {

        int l = 0, h = a.length-1, mid=0;

        while(l <= h)
        {
            mid = (l+h)/2;
            if(key == a[mid]) {
                return mid;
            }
            else if(key < a[mid]) {
                h = mid-1;
//              1 = 1;
            }
            else {
                l = mid+1;
//              h = h;
            }
        }
        return -1;

    }

    public static void main(String[] args) {

        int[] a = {30,51,6,80,12,15,16,19,21};
        Arrays.sort(a);
        int key = 15;
        System.out.println(binarySearch(a,key));

    }
}