import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function FailureRateChart({ periods }) {
  const data = periods.map((p) => ({
    period: p.period,
    failure_rate: +(p.failure_rate * 100).toFixed(2),
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="period" tick={{ fontSize: 11 }} />
        <YAxis unit="%" tick={{ fontSize: 11 }} />
        <Tooltip formatter={(val) => `${val}%`} />
        <Line
          type="monotone"
          dataKey="failure_rate"
          stroke="#ef4444"
          strokeWidth={2}
          dot={false}
          name="Failure Rate"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
