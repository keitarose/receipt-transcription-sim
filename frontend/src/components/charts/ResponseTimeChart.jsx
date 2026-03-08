import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function ResponseTimeChart({ periods }) {
  const data = periods.map((p) => ({
    period: p.period,
    mean_response_time: +p.mean_response_time.toFixed(3),
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="period" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Area
          type="monotone"
          dataKey="mean_response_time"
          stroke="#8b5cf6"
          fill="#ede9fe"
          strokeWidth={2}
          name="Mean Response Time"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
