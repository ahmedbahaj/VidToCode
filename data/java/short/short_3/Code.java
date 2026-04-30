{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset178 GeezaPro;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh9000\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 public class sampleclass \{\
    public static void main(String[] args)\{\
        \
    int arr[]=\{1, 45, 60, 100, 0, 5\};\
    \
    \
     int n = 100;\
     int f=0;\
     \
     for(int i=0; i<arr.length;i++)\
     \
    \{\
         \
       if(arr[i]==n)\
       \{\
           f=1;\
           System.out.printf("Element found in index %d \\n",i); \
           break;\
       \}\
         \
    \}  \
            \
     if(f==0)\
    \{\
      System.out.print("Element not found");\
    \}   \
         \
    \}\
    \
    \
    \
\}}