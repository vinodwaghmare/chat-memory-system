"use client";

export default function HealthBadge({
  name,
  status,
}: {
  name: string;
  status: string;
}) {
  const isOk = status === "ok";
  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-md border ${
        isOk
          ? "border-green-800 bg-green-900/30"
          : "border-red-800 bg-red-900/30"
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full ${isOk ? "bg-green-400" : "bg-red-400"}`}
      />
      <span className="text-sm text-gray-200">{name}</span>
      <span className={`text-xs ${isOk ? "text-green-400" : "text-red-400"}`}>
        {status}
      </span>
    </div>
  );
}
