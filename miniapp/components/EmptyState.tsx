export default function EmptyState({
  icon,
  title,
  subtitle,
}: {
  icon: string;
  title: string;
  subtitle: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <span className="text-5xl mb-4">{icon}</span>
      <h3 className="font-display font-semibold text-navy-500 text-lg">{title}</h3>
      <p className="text-navy-300 text-sm mt-1 max-w-xs">{subtitle}</p>
    </div>
  );
}
