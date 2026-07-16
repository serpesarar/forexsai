"use client";

/**
 * OwnerGuard — yalnızca panel sahiplerinin (OWNER_EMAILS) girişinde içerik
 * gösterir. AuthGuard'ın üstüne kurulur: önce normal oturum kontrolü, sonra
 * e-posta eşleşmesi. Sahip değilse ana panele yönlendirir.
 * NeuralNav, EVOLUTION sekmesini yalnızca useIsOwner() true iken gösterir.
 */

import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import AuthGuard from "@/components/AuthGuard";
import { useAuthStore } from "@/lib/auth/store";

export const OWNER_EMAILS = ["m.canodacioglu@gmail.com", "m.canodaciogluabd@gmail.com"];

function isOwnerEmail(email: string | null | undefined): boolean {
  const normalized = (email ?? "").trim().toLowerCase();
  return OWNER_EMAILS.includes(normalized);
}

export function useIsOwner(): boolean {
  const email = useAuthStore((s) => s.user?.email);
  return isOwnerEmail(email);
}

function OwnerOnly({ children }: { children: ReactNode }) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isOwner = isOwnerEmail(user?.email);

  useEffect(() => {
    // AuthGuard bu noktada oturumu garantiledi; sahip değilse ana panele dön.
    if (user && !isOwner) router.replace("/");
  }, [user, isOwner, router]);

  if (!isOwner) return null;
  return <>{children}</>;
}

export default function OwnerGuard({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <OwnerOnly>{children}</OwnerOnly>
    </AuthGuard>
  );
}
