// Import HTTP Module
const http = require("http");

// Function to create the server
const server = http.createServer((req, res) => {
  // Set the "Content-type" header
  res.setHeader("Content-type", "application/json");

  // JavaScript Object
  const dataObj = {
    name: "Aditya",
    age: 21,
    channel: "Brainstorm Codings",
  };

  //   Convert JavaScript Object into String
  const data = JSON.stringify(dataObj);

  //   Send JSON as response
  res.end(data);
});

// Server listening on port localhost:3000
server.listen("3000", () => {
  console.log("Server is listening on port 3000...");
});