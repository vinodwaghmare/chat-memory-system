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
    <div className="bg-[#262626] border border-[#333] flex items-center gap-2.5 px-3 py-2 rounded-lg transition-colors">
      {/* Status dot */}
      <span
        className={`w-2 h-2 rounded-full ${
          isOk ? "bg-green-400" : "bg-red-400"
        }`}
      />

      <span className="text-sm text-[#e5e5e5] font-medium">{name}</span>
      <span
        className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
          isOk
            ? "text-green-400 bg-green-500/15"
            : "text-red-400 bg-red-500/15"
        }`}
      >
        {status}
      </span>
    </div>
  );
}
