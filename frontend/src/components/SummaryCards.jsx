import { Activity, CheckCircle, XCircle, Coins } from "lucide-react";

export default function SummaryCards({ totals, periods }) {
  const totalArrivals = totals.arrivals ?? 0;
  const totalApprovals = totals.approvals ?? 0;
  const totalRejections = totals.rejections ?? 0;
  const totalFailures = totals.failures ?? 0;
  const totalTokens = totals.tokens ?? 0;

  const approvalRate =
    totalApprovals + totalRejections > 0
      ? ((totalApprovals / (totalApprovals + totalRejections)) * 100).toFixed(1)
      : "0.0";

  const failureRate =
    totalArrivals > 0
      ? ((totalFailures / totalArrivals) * 100).toFixed(1)
      : "0.0";

  const cards = [
    {
      label: "Total Arrivals",
      value: totalArrivals.toLocaleString(),
      icon: Activity,
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      label: "Approval Rate",
      value: `${approvalRate}%`,
      icon: CheckCircle,
      color: "text-green-600",
      bg: "bg-green-50",
    },
    {
      label: "Failure Rate",
      value: `${failureRate}%`,
      icon: XCircle,
      color: "text-red-600",
      bg: "bg-red-50",
    },
    {
      label: "Total Tokens",
      value: totalTokens.toLocaleString(),
      icon: Coins,
      color: "text-amber-600",
      bg: "bg-amber-50",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className={`p-1.5 rounded-lg ${card.bg}`}>
              <card.icon className={`w-4 h-4 ${card.color}`} />
            </div>
            <span className="text-xs text-gray-500 font-medium">
              {card.label}
            </span>
          </div>
          <p className="text-2xl font-bold text-gray-800">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
