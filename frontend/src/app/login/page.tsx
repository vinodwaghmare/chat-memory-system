"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { googleLogin, isLoggedIn } from "@/lib/api";
import { Brain } from "lucide-react";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const buttonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isLoggedIn()) {
      router.replace("/");
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (!(window as any).google) return;
      (window as any).google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleResponse,
      });
      if (buttonRef.current) {
        (window as any).google.accounts.id.renderButton(buttonRef.current, {
          theme: "filled_black",
          size: "large",
          text: "signin_with",
          shape: "rectangular",
          width: 300,
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      script.remove();
    };
  }, []);

  async function handleGoogleResponse(response: any) {
    setLoading(true);
    setError("");
    try {
      await googleLogin(response.credential);
      router.replace("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  // Expose to Google callback
  useEffect(() => {
    (window as any).__handleGoogleResponse = handleGoogleResponse;
  }, []);

  return (
    <div className="min-h-screen bg-[#1a1a1a] flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="bg-[#262626] border border-[#333] rounded-xl p-8">
          {/* Brand */}
          <div className="flex flex-col items-center mb-8">
            <Brain className="w-10 h-10 text-blue-400 mb-3" />
            <h1 className="text-xl font-bold text-white">Chat Memory System</h1>
            <p className="text-sm text-[#a3a3a3] mt-1">Sign in to continue</p>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-6">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Google Sign-In Button */}
          <div className="flex justify-center">
            {loading ? (
              <p className="text-sm text-[#a3a3a3]">Signing in...</p>
            ) : (
              <div ref={buttonRef} />
            )}
          </div>

          {/* Footer */}
          <p className="text-[11px] text-[#666] text-center mt-8">
            Your memories are private and isolated to your account
          </p>
        </div>
      </div>
    </div>
  );
}
