import { TopHeader } from "@/components/user/TopHeader";
import { BottomNav } from "@/components/user/BottomNav";

export default function UserLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background flex flex-col justify-between">
      <div className="w-full max-w-md mx-auto flex flex-col flex-1 pb-20 shadow-xl border-x border-border/30 bg-card/30">
        <TopHeader />
        <main className="flex-1 px-4 py-4">{children}</main>
        <BottomNav />
      </div>
    </div>
  );
}
