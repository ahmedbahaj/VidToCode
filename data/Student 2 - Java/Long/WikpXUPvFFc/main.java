package cookie;

import java.util.Scanner;
import java.util.Random;
public class Cookie {


    public static void main(String[] args) {
        Scanner scan = new Scanner(System.in);
        Random rand = new Random();
        int userScore = 0;
        int cpuScore = 0;

        while(true){
            System.out.println("enter 1 for 2 for paper and 3 for scissors");
            int userChoice = scan.nextInt();
            int cpuChoice = rand.nextInt(3) +1;


            if(cpuChoice == userChoice){
                System.out.println("Tie. no points will be awarded");

            }else if(userChoice == 1){
                if(cpuChoice == 2){
                    System.out.println("Cpu chose paper and u have lost this round");
                    cpuScore++;
                    System.out.printf("CPU score: %d\n User score: %d\n", cpuScore, userScore);

                }else if(cpuChoice == 3){
                    System.out.println("Cpu chose scissors and u have won this round");
                    userScore++;
                    System.out.printf("CPU score: %d\n User score: %d\n", cpuScore, userScore);

                }

            }else if(userChoice == 2){
                if(cpuChoice == 1){
                    System.out.println("Cpu chose rock and u have won this round");
                    userScore++;
                    System.out.printf("CPU score: %d\n User score: %d\n", cpuScore, userScore);

                }else if(cpuChoice == 3){
                    System.out.println("Cpu chose scissors and u have lost this round");
                    cpuScore++;
                    System.out.printf("CPU score: %d\n User score: %d\n", cpuScore, userScore);

                }

            }else if (userChoice == 3){
                if(cpuChoice == 1){
                    System.out.println("Cpu chose rock and u have lost this round");
                    cpuScore++;
                    System.out.printf("CPU score: %d\n User score: %d\n", cpuScore, userScore);

                }else if(cpuChoice == 2){
                    System.out.println("Cpu chose paperand u have won this round");
                    userScore++;
                    System.out.printf("CPU score: %d\n User score: %d\n", cpuScore, userScore);

                }

            }
            if (cpuScore == 2){
                System.out.println("sorry but you have lost best 2 out of 3");
                System.out.printf("CPU score: %d\n User score: %d\n", cpuScore, userScore);
                break;




            }if (userScore == 2){
                System.out.println("congrats you have won best 2 out of 3");
                System.out.printf("CPU score: %d\n User score: %d\n", cpuScore, userScore);
                break;
            }


        }}}