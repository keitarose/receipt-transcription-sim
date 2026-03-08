import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function TokensChart({ periods }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={periods}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="period" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Bar
          dataKey="total_tokens"
          fill="#f59e0b"
          radius={[3, 3, 0, 0]}
          name="Tokens"
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
