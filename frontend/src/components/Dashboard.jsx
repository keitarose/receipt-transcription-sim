import { ArrowLeft } from "lucide-react";
import SummaryCards from "./SummaryCards";
import ArrivalsChart from "./charts/ArrivalsChart";
import FailureRateChart from "./charts/FailureRateChart";
import ApprovalRateChart from "./charts/ApprovalRateChart";
import ResponseTimeChart from "./charts/ResponseTimeChart";
import TokensChart from "./charts/TokensChart";
import CorrectionRateChart from "./charts/CorrectionRateChart";

export default function Dashboard({ data, onReset }) {
  const { periods = [], totals = {} } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Simulation Results
        </h2>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Load another file
        </button>
      </div>

      <SummaryCards totals={totals} periods={periods} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Arrivals per Period">
          <ArrivalsChart periods={periods} />
        </ChartCard>

        <ChartCard title="Failure Rate">
          <FailureRateChart periods={periods} />
        </ChartCard>

        <ChartCard title="Approval Rate">
          <ApprovalRateChart periods={periods} />
        </ChartCard>

        <ChartCard title="Mean Response Time">
          <ResponseTimeChart periods={periods} />
        </ChartCard>

        <ChartCard title="Tokens Awarded per Period">
          <TokensChart periods={periods} />
        </ChartCard>

        <ChartCard title="Correction Rate">
          <CorrectionRateChart periods={periods} />
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <h3 className="text-sm font-medium text-gray-600 mb-4">{title}</h3>
      {children}
    </div>
  );
}
