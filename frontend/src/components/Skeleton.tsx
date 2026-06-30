export function SkeletonLine({ className = "" }: { className?: string }) {
  return <div className={`skeleton-shimmer rounded-md ${className}`} />;
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-5">
      <SkeletonLine className="h-12 w-72" />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <SkeletonLine key={item} className="h-32" />
        ))}
      </div>
      <SkeletonLine className="h-72" />
    </div>
  );
}
