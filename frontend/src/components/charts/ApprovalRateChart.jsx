import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function ApprovalRateChart({ periods }) {
  const data = periods.map((p) => ({
    period: p.period,
    approval_rate: +(p.approval_rate * 100).toFixed(2),
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="period" tick={{ fontSize: 11 }} />
        <YAxis unit="%" tick={{ fontSize: 11 }} domain={[0, 100]} />
        <Tooltip formatter={(val) => `${val}%`} />
        <Line
          type="monotone"
          dataKey="approval_rate"
          stroke="#22c55e"
          strokeWidth={2}
          dot={false}
          name="Approval Rate"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
