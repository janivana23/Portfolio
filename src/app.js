import { useEffect, useState } from "react";

function App() {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    fetch("https://singapore-mrt-web.azurewebsites.net/data")
      .then(res => res.json())
      .then(data => setRows(data));
  }, []);

  return (
    <div>
      <h1>Oracle Data</h1>
      <table border="1">
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((col, j) => <td key={j}>{col}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
