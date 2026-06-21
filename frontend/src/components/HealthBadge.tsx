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
      className={`glass flex items-center gap-2.5 px-3.5 py-2 rounded-xl transition-all duration-300 ${
        isOk ? "hover:glow-green" : "hover:glow-red"
      }`}
    >
      {/* Pulsing status dot */}
      <span className="relative flex h-2.5 w-2.5">
        <span
          className={`absolute inset-0 rounded-full animate-ping opacity-40 ${
            isOk ? "bg-green-400" : "bg-red-400"
          }`}
        />
        <span
          className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
            isOk ? "bg-green-400" : "bg-red-400"
          }`}
        />
      </span>

      <span className="text-sm text-gray-300 font-medium">{name}</span>
      <span
        className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
          isOk
            ? "text-green-300 bg-green-500/10"
            : "text-red-300 bg-red-500/10"
        }`}
      >
        {status}
      </span>
    </div>
  );
}
