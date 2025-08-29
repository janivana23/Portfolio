const express = require("express");
const oracledb = require("oracledb");
const cors = require("cors");

const app = express();
app.use(cors());

async function runQuery(sql) {
  let conn;
  try {
    conn = await oracledb.getConnection({
      user: "jiva0003",
      password: "tutor2025",
      connectString: "fit-oracle-pt01.mpc.monash.edu:1521/FITUGDB.fit-oracle-pt01.mpc.monash.edu"
    });
    const result = await conn.execute(sql);
    return result.rows;
  } finally {
    if (conn) await conn.close();
  }
}

app.get("/data", async (req, res) => {
  const rows = await runQuery("SELECT * FROM your_table");
  res.json(rows);
});

app.listen(7071, () => console.log("API running on http://localhost:7071"));
