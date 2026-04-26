function rollTheDice(){
    result = Math.floor(Math.random()* 6 + 1);
    alert(result);
    let playAgain = prompt("play again?");
    if(playAgain === "yes"){
        rollTheDice();
    }
    else if (playAgain === "no"){
        alert("Bye");
    }
}

if(prompt("Let's play!") === "roll"){
rollTheDice()
}