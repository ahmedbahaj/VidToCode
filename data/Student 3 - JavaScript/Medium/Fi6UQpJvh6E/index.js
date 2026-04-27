
var fs = require('fs')
fs.readFile('readExcel.js','utf8',function(err,data){
    console.log(data);
});
fs.writeFile('write.js',"console.log('File created')",function(err){
    console.log("Data is saved");
});
fs.appendFile('write.js',"console.log('File created')",function(err){
    console.log("Data is saved");
});
fs.unlink('write.js',function(err){
    console.log("File Deleted");
});
