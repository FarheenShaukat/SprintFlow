"use client";

import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const velocity = [
  { sprint: "S20", done: 28, health: 74 },
  { sprint: "S21", done: 33, health: 81 },
  { sprint: "S22", done: 37, health: 86 },
  { sprint: "S23", done: 39, health: 88 },
  { sprint: "S24", done: 42, health: 91 }
];

const fallbackPriority = [
  { name: "Low", tasks: 0 },
  { name: "Medium", tasks: 0 },
  { name: "High", tasks: 0 },
  { name: "Critical", tasks: 0 }
];

export function VelocityChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={velocity}>
        <CartesianGrid stroke="#e4e1ee" strokeDasharray="4 4" />
        <XAxis dataKey="sprint" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="done" stroke="#3525cd" strokeWidth={3} />
        <Line type="monotone" dataKey="health" stroke="#0058be" strokeWidth={3} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function PriorityChart({ data = fallbackPriority }: { data?: { name: string; tasks: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid stroke="#e4e1ee" strokeDasharray="4 4" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="tasks" fill="#4f46e5" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
