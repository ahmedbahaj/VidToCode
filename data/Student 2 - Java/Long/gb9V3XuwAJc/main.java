/*
 * THIS IS METHOD OVERLOADING
 */
// class Addition {
//     int add(int n1, int n2) {
//         return n1 + n2;
//     }
//
//     int add(int n1, int n2, int n3) {
//         return n1 + n2 + n3;
//     }
//
//     double add(int n1, int n2, int n3, int n4) {
//         return n1 + n2 + n3 + n4;
//     }
// }

/**
 * THIS IS METHOD OVERRIDING
 *
 */
class A {
    void show() {
        System.out.println("THIS IS CLASS A");
    }
}

class B extends A {
    void show() {
        // super.show();
        System.out.println("THIS IS CLASS B");
    }
}

public class Demo {
    public static void main(String[] args) {
        // Addition obj = new Addition();
        // int add1 = obj.add(10, 2);
        // int add2 = obj.add(5, 6, 5);
        // double add3 = obj.add(8, 9, 2, 3);

        // System.out.println(add1 + " " + add2 + " " + add3);

        B obj = new B();
        obj.show();
    }
}