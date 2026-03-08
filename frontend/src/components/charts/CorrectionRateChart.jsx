import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function CorrectionRateChart({ periods }) {
  const data = periods.map((p) => ({
    period: p.period,
    correction_rate: +(p.correction_rate * 100).toFixed(2),
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
          dataKey="correction_rate"
          stroke="#0ea5e9"
          strokeWidth={2}
          dot={false}
          name="Correction Rate"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
