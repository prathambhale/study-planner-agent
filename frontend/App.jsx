import React, { useState } from "react";

export default function App() {
  const [subjectsText, setSubjectsText] = useState("CSA,DE,OOP");
  const [startDate, setStartDate] = useState("");
  const [hours, setHours] = useState(3);
  const [plan, setPlan] = useState(null);

  async function createPlan() {
    const subs = subjectsText.split(",").map((s) => ({
      name: s.trim(),
      weight: 3,
    }));

    const payload = {
      user_id: "user1",
      subjects: subs,
      start_date:
        startDate || new Date().toISOString().slice(0, 10),
      hours_per_day: Number(hours),
      session_length_minutes: 50,
    };

    const res = await fetch("http://127.0.0.1:8000/create-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (data.plan_id) {
      const planRes = await fetch(
        `http://127.0.0.1:8000/get-plan?plan_id=${data.plan_id}`
      );
      const planJson = await planRes.json();
      setPlan(planJson);
    }
  }

  if (!plan) {
    return (
      <div style={{ padding: "20px" }}>
        <h1>Study Planner</h1>
        <label>Subjects (comma separated)</label> <br />
        <input
          value={subjectsText}
          onChange={(e) => setSubjectsText(e.target.value)}
        />
        <br />
        <label>Start Date</label> <br />
        <input
          type="date"
          onChange={(e) => setStartDate(e.target.value)}
        />
        <br />
        <label>Hours per day</label> <br />
        <input
          type="number"
          value={hours}
          onChange={(e) => setHours(e.target.value)}
        />
        <br />
        <button onClick={createPlan}>Create Plan</button>
      </div>
    );
  }

  return (
    <div style={{ padding: "20px" }}>
      <h1>Your Study Plan</h1>

      {plan.sessions.map((s) => (
        <div
          key={s.session_uuid}
          style={{
            border: "1px solid black",
            margin: "8px",
            padding: "8px",
            borderRadius: "6px",
          }}
        >
          <b>{s.date}</b> — {s.subject} — {s.minutes} mins
        </div>
      ))}
    </div>
  );
}
