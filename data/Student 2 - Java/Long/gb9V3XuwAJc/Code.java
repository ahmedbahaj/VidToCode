{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset178 GeezaPro;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh9000\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 /*\
* This IS METHOD OVERLOADING\
*/\
class Addition \{\
    \
    int add(int n1 , int n2)\{\
        return n1 + n2;  \
    \}\
    int add(int n1 , int n2 , int n3)\{\
        return n1 + n2 + n3;  \
    \}\
    double add(int n1 , int n2 , int n3 , int n4)\{\
        return n1 + n2 + n3 + n4;  \
    \}\
\}   \
\
\
/*\
* This IS METHOD OVERRIDING\
*/\
\
// class A\{\
 //void show()\{\
     //System.out.println("THIS IS CLASS A");\
     \
 //\}   \
       \
//\}\
\
//class B extends A\{\
    //void show()\{\
     //System.out.println("THIS IS CLASS B");\
     \
 //\}\
    \
//\}\
\
public class Demo \{\
    public static void main(String[] args) \{\
        Addition obj = new Addition();\
        int add1 = obj.add(10, 2);\
        int add2 = obj.add(5, 6, 5);\
        double add3 = obj.add(8, 9, 2, 3);\
        \
        System.out.println(add1 + "" + add2 + "" + add3); \
       \
      // B obj = new B();\
      // obj.show();\
    \}\
    \
\}\
\
        }