//0, 1, 1, 2, 3, 5, 8, 13, 21, 34
function fibonacciIterative(n) {
    let first = 0;
    let second = 1;
  
    let answer = 0;
  
    if(n < 1){
      return first;
    }
  
    if(n === 1){
      return second;
    }
  
    for(let i = 1; i < n; i++){
      answer = first + second;
  
      first = second;
      second = answer;
    }
  
    return answer;
  }
  
  const fibonacciRecursive = (function(n){
  
    let cache = {}
  
    return function(n){
  
    if(n in cache){
      return cache[n];
    }else{
      if(n < 2){
      return n
    }
      cache[n] = fibonacciRecursive(n - 1) + fibonacciRecursive(n - 2);
      return cache[n];
    }
  
    }
  })();
  
  function factorialIterative(n) {
    let answer = 1;
  
    for(let i = 2; i <= n; i++){
      answer *= i;
    }
  
    return answer;
  }
  
  const factorialRecursive = (function(n){
    let cache = {};
  
    return function(n){
      if(n === 2){
        return 2;
      }else{
        if(n in cache){
          return cache[n]
        }else{
          cache[n] = n * factorialRecursive(n - 1);
          return cache[n];
        }
      }
    }
  })();
  
  factorialRecursive(5)