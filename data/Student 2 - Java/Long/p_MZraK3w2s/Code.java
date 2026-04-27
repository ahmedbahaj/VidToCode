{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset178 GeezaPro;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh9000\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import java.util.Arrays;\
import java.util.Scanner;\
\
public class Searching \{\
\
    
    public static int binarySearch(int[] a, int key) \{\
        \
        int l = 0, h = a.length-1, mid = 0;\
\
        while (l <= h) \
        \{\
             mid = (l + h) / 2;\
\
            if (key == a[mid]) \{\
                return mid; 
            \} \
            else if (key < a[mid] ) \{\
                h = mid - 1;\
 //               l = l;\
            \} else \{\
                l = mid + 1;\
 //               h = h;\
            \}\
        \}\
        return -1; \
    \}\
\
    public static void main(String[] args) \{\
\
        int[] a = \{3, 5, 6, 8, 12, 15, 16, 19, 21\};\
        int key = 15;\
        System.out.println(binarySearch(a,key));\
    \}\
\}\
}