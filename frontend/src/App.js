import React from "react";
import "./App.css";

console.log("App.js loaded");

function App() {
  console.log("App function called");
  return (
    <div style={{ backgroundColor: '#09090b', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <h1 style={{ color: 'white', fontSize: '24px' }}>MotivAction is Working!</h1>
    </div>
  );
}

export default App;
