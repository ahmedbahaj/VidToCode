{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset178 GeezaPro;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh9000\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \
import java.util.Random;\
import java.util.Scanner;\
\
public class Cookie \{\
\
    public static void main(String[] args) \{\
        Scanner scan = new Scanner(System.in);\
        Random rand = new Random();\
\
        int userScore = 0;\
        int cpuScore = 0;\
\
        while (true) \{\
\
            System.out.println("Enter 1 for 2 for paper and 3 for scissors");\
            int userChoice = scan.nextInt();\
            int cpurChoice = rand.nextInt(3) + 1;\
\
            if (cpurChoice == userChoice) \{\
                System.out.println("Tie. no points will be awarded");\
\
            \} else if (userChoice == 1) \{\
\
                if (cpurChoice == 2) \{\
                    System.out.println("Cpu chose paper and u have lost this round");\
                    cpuScore++;\
                    System.out.printf("CPU score: %d\\n User score: %d\\n", cpuScore, userScore);\
\
                \} else if (cpurChoice == 3) \{\
\
                    System.out.println("Cpu chose scissors and u have lost this round");\
                    userScore++;\
                    System.out.printf("CPU score: %d\\n User score: %d\\n", cpuScore, userScore);\
                \}\
\
            \} else if (userChoice == 2) \{\
                if (cpurChoice == 1) \{\
                    System.out.println("Cpu chose rock and u have won this round");\
                    userScore++;\
                    System.out.printf("CPU score: %d\\n User score: %d\\n", cpuScore, userScore);\
\
                \} else if (cpurChoice == 3) \{\
\
                    System.out.println("Cpu chose scissors and u have lost this round");\
                    cpuScore++;\
                    System.out.printf("CPU score: %d\\n User score: %d\\n", cpuScore, userScore);\
\
                \} else if (userChoice == 3) \{\
                    if (cpurChoice == 1) \{\
                        System.out.println("Cpu chose rock and u have lost this round");\
                        cpuScore++;\
                        System.out.printf("CPU score: %d\\n User score: %d\\n", cpuScore, userScore);\
\
                    \} else if (cpurChoice == 2) \{\
\
                        System.out.println("Cpu chose paper and u have lost this round");\
                        userScore++;\
                        System.out.printf("CPU score: %d\\n User score: %d\\n", cpuScore, userScore);\
                    \}\
\
                \}\
            \}\
            \
            if(cpuScore == 2)\{\
                System.out.println("sorry but you have lost best 2 out of 3");\
                System.out.printf("CPU score: %d\\n User score: %d\\n", cpuScore, userScore);\
                break;\
            \}\
            if(userScore == 2)\{\
                System.out.println("congrats you have won best 2 out of 3");\
                System.out.printf("CPU score: %d\\n User score: %d\\n", cpuScore, userScore);\
                break;\
            \}\
        \}\
    \}\
\}\
}