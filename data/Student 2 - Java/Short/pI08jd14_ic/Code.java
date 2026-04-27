{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset178 GeezaPro;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh9000\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import java.util.Scanner;\
\
public class JavaTestClass\{\
    public static void main(String[] args) \{\
        int operator,n1 ,n2;\
        System.out.println("1 - Add\\n" +"2 - Subtract\\n" +"3 - Multiply\\n" +"4 - Divide");\
        System.out.println("Choose Operator: ");\
        Scanner sc = new Scanner(System.in);\
        operator = sc.nextInt();\
        System.out.println("Enter first number: ");\
        n1 = sc.nextInt();\
        System.out.println("Enter second number: ");\
        n2 = sc.nextInt();\
        \
        int result = 0;\
        switch(operator)\{\
            case 1:\
                result = n1 + n2;\
                break;\
                \
            case 2:\
                 result = n1 - n2;\
                break;\
                \
            case 3: \
                 result = n1 * n2;\
                break;\
                \
            case 4: \
                 result = n1 / n2;\
                break;\
                \
                default:\
                    System.out.println("Enterd operator is not vaild");\
        \}\
        \
        System.out.println("Result is : " + result);    \
    \}\
\}}