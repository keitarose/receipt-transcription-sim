import { useCallback, useState } from "react";
import Dashboard from "./components/Dashboard";
import FileUpload from "./components/FileUpload";
import { Receipt } from "lucide-react";

export default function App() {
  const [data, setData] = useState(null);

  const handleData = useCallback((parsed) => {
    setData(parsed);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center gap-3">
          <Receipt className="w-7 h-7 text-indigo-600" />
          <h1 className="text-xl font-semibold text-gray-800">
            Receipt Transcription Simulation Dashboard
          </h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {data === null ? (
          <FileUpload onData={handleData} />
        ) : (
          <Dashboard data={data} onReset={() => setData(null)} />
        )}
      </main>
    </div>
  );
}
