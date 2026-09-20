<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aplikasi Kalkulator Sederhana</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
    }

    body {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background-color: #f4f4f9;
    }

    .calculator {
      background-color: #22252d;
      padding: 20px;
      border-radius: 16px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
      width: 320px;
    }

    .display {
      width: 100%;
      height: 60px;
      background-color: #2a2d37;
      color: #ffffff;
      text-align: right;
      padding: 10px 15px;
      font-size: 2rem;
      border: none;
      border-radius: 8px;
      margin-bottom: 20px;
      outline: none;
    }

    .buttons {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }

    button {
      padding: 15px;
      font-size: 1.2rem;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      background-color: #292d36;
      color: #fff;
      transition: background-color 0.2s ease;
    }

    button:hover {
      background-color: #353b48;
    }

    button.operator {
      color: #eb4d4b;
    }

    button.clear {
      color: #2ed573;
    }

    button.equal {
      background-color: #eb4d4b;
      color: #fff;
      grid-column: span 2;
    }

    button.equal:hover {
      background-color: #ff5252;
    }
  </style>
</head>
<body>

  <div class="calculator">
    <input type="text" class="display" id="display" disabled>
    <div class="buttons">
      <button class="clear" onclick="clearDisplay()">C</button>
      <button onclick="deleteLast()">DEL</button>
      <button class="operator" onclick="appendCharacter('/')">/</button>
      <button class="operator" onclick="appendCharacter('*')">×</button>

      <button onclick="appendCharacter('7')">7</button>
      <button onclick="appendCharacter('8')">8</button>
      <button onclick="appendCharacter('9')">9</button>
      <button class="operator" onclick="appendCharacter('-')">-</button>

      <button onclick="appendCharacter('4')">4</button>
      <button onclick="appendCharacter('5')">5</button>
      <button onclick="appendCharacter('6')">6</button>
      <button class="operator" onclick="appendCharacter('+')">+</button>

      <button onclick="appendCharacter('1')">1</button>
      <button onclick="appendCharacter('2')">2</button>
      <button onclick="appendCharacter('3')">3</button>
      <button class="equal" onclick="calculateResult()">=</button>

      <button onclick="appendCharacter('0')" style="grid-column: span 2;">0</button>
      <button onclick="appendCharacter('.')">.</button>
    </div>
  </div>

  <script>
    const display = document.getElementById('display');

    function appendCharacter(char) {
      display.value += char;
    }

    function clearDisplay() {
      display.value = '';
    }

    function deleteLast() {
      display.value = display.value.slice(0, -1);
    }

    function calculateResult() {
      try {
        if (display.value.trim() === '') return;
        display.value = eval(display.value);
      } catch (error) {
        display.value = 'Error';
        setTimeout(clearDisplay, 1500);
      }
    }
  </script>

</body>
</html>
